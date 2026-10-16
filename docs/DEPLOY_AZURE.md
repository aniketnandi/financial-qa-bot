# Deploying to Azure Container Apps with Azure OpenAI

This guide deploys the FastAPI service (`/ask`, `/ask_agent`) as a public HTTPS endpoint on **Azure Container Apps**, with **Azure OpenAI** as the LLM. Everything else (retrieval, prompts, tools, the agent loop) is the same code that runs locally with Gemini.

```
GitHub Actions ──build + smoke test──► ghcr.io/aniketnandi/financial-qa-bot  (image with FAISS index + MiniLM baked in)
                                                    │ pull
                                                    ▼
          Azure Container Apps (1 vCPU / 2 GiB, scale 0–1) ──► Azure OpenAI deployment "chat" (gpt-4.1-mini)
                   ▲  HTTPS + X-API-Key
               clients / eval harness
```

It costs very little on Azure for Students: the app scales to zero when idle, the image comes free from GitHub Container Registry (no paid Azure Container Registry), and Azure OpenAI is billed per token with a small rate cap.

## 0. Prerequisites

- An Azure subscription (Azure for Students works).
- The image published by CI. On every push, the `docker` job in `.github/workflows/ci.yml` builds the image, smoke-tests it and pushes `ghcr.io/aniketnandi/financial-qa-bot:<commit-sha>`. Pushes to `main` also update `:latest`. To deploy a branch before merging, use its commit-sha tag as `IMAGE`.
- **Make the image public, once.** On GitHub, open your profile → **Packages** → `financial-qa-bot` → **Package settings** → **Change visibility** → **Public**. Azure can then pull it without registry credentials. The image contains only code, the public 10-K and the index; no secrets.

Run everything below in **Azure Cloud Shell** (the `>_` icon in the portal's top bar; choose **Bash**, and pick **No storage account required** on first launch).

### Student / university subscriptions

These four things blocked the first deployment on an Azure for Students subscription under a university tenant. The commands below already handle them:

| Problem | Symptom | Handled by |
|---|---|---|
| `az` defaults to another subscription you can see (e.g. a university one) | `AuthorizationFailed` on `register/action` or `resourcegroups/write` | `az account set --subscription "Azure for Students"` (re-run after every Cloud Shell restart) |
| The university requires tags on resource groups | `RequestDisallowedByPolicy` naming `Owner`, `Cost Center`, `IaC managed` | `--tags "${TAGS[@]}"` on every create |
| The student offer allows only a few regions | `RequestDisallowedByAzure` "best available regions" | List them with the `az policy assignment list` command in step 1, then pick from it |
| Chat-model quota exists only in some allowed regions | `InvalidResourceProperties` "SKU … not supported in this region" | Check `az cognitiveservices usage list` (step 2) and put Azure OpenAI where the quota is |

## 1. Variables and providers

```bash
az account set --subscription "Azure for Students"
az account show --query name -o tsv            # must print the subscription you expect

# Regions this subscription may deploy to (student offers restrict these)
az policy assignment list --disable-scope-strict-match \
  --query "[?parameters.listOfAllowedLocations].parameters.listOfAllowedLocations.value" -o tsv

RG=financial-qa-rg
LOC=canadacentral                # Container Apps region: one of the allowed regions above
AOAI_LOC=francecentral           # Azure OpenAI region: where you have chat-model quota (step 2)
AOAI=fqa-openai-$RANDOM          # must be globally unique
ENVNAME=fqa-env
APP=financial-qa-bot
IMAGE=ghcr.io/aniketnandi/financial-qa-bot:latest
TAGS=("Owner=you@university.edu" "Cost Center=Student" "IaC managed=aniketnandi/financial-qa-bot")

az extension add --name containerapp --upgrade
for ns in Microsoft.CloudShell Microsoft.App Microsoft.OperationalInsights Microsoft.CognitiveServices; do
  az provider register --namespace $ns --wait
done
az group create -n $RG -l $LOC --tags "${TAGS[@]}"
```

`TAGS` only matters if a policy requires tags. If yours doesn't, it does no harm.

Cloud Shell variables are lost when the session times out. If that happens, re-run the variable lines, then set `AOAI` to the name the first run actually created.

## 2. Azure OpenAI resource and model deployment

Check quota **before** creating anything. The model catalog lists models you may have no quota for:

```bash
# Non-zero chat-model rows (e.g. OpenAI.GlobalStandard.gpt4.1-mini) = deployable here
az cognitiveservices usage list -l $AOAI_LOC \
  --query "[?contains(name.value, 'OpenAI') && limit > \`0\`].{quota:name.value, limit:limit}" -o table
```

If the table shows only fine-tuning, transcription and embedding rows, try another allowed region.

```bash
az cognitiveservices account create -n $AOAI -g $RG -l $AOAI_LOC \
  --kind OpenAI --sku S0 --custom-domain $AOAI --tags "${TAGS[@]}" --yes

# Deployment named "chat". The live deployment uses gpt-4.1-mini (fast, non-reasoning, reliable tool calling).
# Capacity 50 = 50K tokens/minute: one agent question makes 3-4 calls of ~2-8K tokens each,
# so 10K TPM rate-limits a single question. Billing is per token, so the cap costs nothing.
az cognitiveservices account deployment create -n $AOAI -g $RG \
  --deployment-name chat --model-name gpt-4.1-mini --model-version 2025-04-14 \
  --model-format OpenAI --sku-name GlobalStandard --sku-capacity 50

ENDPOINT=$(az cognitiveservices account show -n $AOAI -g $RG --query properties.endpoint -o tsv)
AOAI_KEY=$(az cognitiveservices account keys list -n $AOAI -g $RG --query key1 -o tsv)
```

If the model or version isn't offered in your region, list the alternatives with `az cognitiveservices account list-models -n $AOAI -g $RG -o table`, and pick a small non-reasoning chat model you have quota for. Whatever you deploy, name the deployment `chat`.

## 3. Container Apps environment and app

```bash
az containerapp env create -n $ENVNAME -g $RG -l $LOC --tags "${TAGS[@]}"

API_KEY=$(openssl rand -hex 16)
echo "Save this API key: $API_KEY"

az containerapp create -n $APP -g $RG --environment $ENVNAME \
  --image $IMAGE --target-port 8000 --ingress external \
  --cpu 1 --memory 2Gi --min-replicas 0 --max-replicas 1 \
  --tags "${TAGS[@]}" \
  --secrets aoai-key="$AOAI_KEY" api-key="$API_KEY" \
  --env-vars LLM_PROVIDER=azure_openai AZURE_OPENAI_ENDPOINT="$ENDPOINT" \
             AZURE_OPENAI_DEPLOYMENT=chat AZURE_OPENAI_API_KEY=secretref:aoai-key \
             API_KEY=secretref:api-key

URL=https://$(az containerapp show -n $APP -g $RG --query properties.configuration.ingress.fqdn -o tsv)
echo $URL
```

The keys are stored as Container Apps **secrets** and referenced with `secretref:`, so they never appear in the image or in plain environment variables.

## 4. Test it

```bash
curl $URL/                       # {"status":"ok", ..., "llm_provider":"azure_openai"}

curl -X POST $URL/ask_agent -H "Content-Type: application/json" -H "X-API-Key: $API_KEY" \
  -d '{"question": "What was Tesla'\''s net profit margin in 2023?"}'
```

The first request after the app has been idle takes about 30–60 s while a replica starts and loads the embedding model. Later requests are fast. `$URL/docs` serves the Swagger UI. Each POST endpoint there has an `x-api-key` field: paste the key, then **Try it out**.

## 5. Run the eval against the deployment

From Cloud Shell, where `$URL` and `$API_KEY` are already set. The eval only needs `requests`:

```bash
git clone -q https://github.com/aniketnandi/financial-qa-bot.git && cd financial-qa-bot
pip install -q --user requests
python3 evals/eval_qa.py --base-url $URL --api-key "$API_KEY" \
  --endpoint rag=/ask --golden evals/golden_set.jsonl --out evals/results_azure_rag --sleep 1
python3 evals/eval_qa.py --base-url $URL --api-key "$API_KEY" \
  --endpoint agent=/ask_agent --golden evals/golden_set.jsonl --out evals/results_azure_agent --sleep 1
```

Cloud Shell can't push to GitHub without setting up credentials. Copy `results.jsonl` out with `cat`, or run the same commands from a local clone.

Commit the two results folders. They are the Azure OpenAI numbers. The existing `results_rag/` and `results_agent/` folders are Gemini runs.

## 6. Updating after a code change

Push to `main`, wait for CI to publish the image, then roll a new revision with that commit's tag:

```bash
az containerapp update -n $APP -g $RG --image ghcr.io/aniketnandi/financial-qa-bot:<commit-sha>
```

## 7. Cost controls

- **Budget alert:** in the portal, go to **Cost Management → Budgets → Add**, for example $10/month with an email alert at 50%.
- **Rate cap:** the `--sku-capacity 50` deployment allows at most 50K tokens/minute. A RAG call is roughly 2–3K tokens, and a full 40-request eval costs a few cents with `gpt-4.1-mini`.
- **Scale to zero:** keep `--min-replicas 0`. A permanently warm replica removes cold starts, but it would use up a large share of the student credit each month.
- **Tear down everything:** `az group delete -n $RG --yes`

## Troubleshooting

| Symptom | Fix |
|---|---|
| Container stuck pulling the image / `unauthorized` | Make the GHCR package public (step 0) |
| `AuthorizationFailed` / `RequestDisallowedByPolicy` / `RequestDisallowedByAzure` | See *Student / university subscriptions* above |
| `/ask` returns 502 | Check the deployment name is `chat`, and the endpoint and key secrets. View logs: `az containerapp logs show -n $APP -g $RG --follow` |
| 404 `DeploymentNotFound` | The model deployment is still provisioning; wait a minute |
| API version errors | Set `AZURE_OPENAI_API_VERSION` to a version your resource supports: `az containerapp update -n $APP -g $RG --set-env-vars AZURE_OPENAI_API_VERSION=<version>` |
| Out-of-memory restarts | `az containerapp update -n $APP -g $RG --cpu 2 --memory 4Gi` |

# Deploying to Azure Container Apps with Azure OpenAI

This guide deploys the FastAPI service (`/ask`, `/ask_agent`) as a public HTTPS endpoint on **Azure Container Apps**, with **Azure OpenAI** as the LLM. Everything else (retrieval, prompts, tools, the agent loop) is the same code that runs locally with Gemini.

```
GitHub Actions ──build + smoke test──► ghcr.io/aniketnandi/financial-qa-bot  (image with FAISS index + MiniLM baked in)
                                                    │ pull
                                                    ▼
          Azure Container Apps (1 vCPU / 2 GiB, scale 0–1) ──► Azure OpenAI deployment ("chat")
                   ▲  HTTPS + X-API-Key
               clients / eval harness
```

It costs very little on Azure for Students: the app scales to zero when idle, the image comes free from GitHub Container Registry (no paid Azure Container Registry), and Azure OpenAI is billed per token with a small rate cap.

## 0. Prerequisites

- An Azure subscription (Azure for Students works).
- The image published by CI. On every push, the `docker` job in `.github/workflows/ci.yml` builds the image, smoke-tests it and pushes `ghcr.io/aniketnandi/financial-qa-bot:<commit-sha>`. Pushes to `main` also update `:latest`. To deploy a branch before merging, use its commit-sha tag as `IMAGE`.
- **Make the image public, once.** On GitHub, open your profile → **Packages** → `financial-qa-bot` → **Package settings** → **Change visibility** → **Public**. Azure can then pull it without registry credentials. The image contains only code, the public 10-K and the index; no secrets.

Run everything below in **Azure Cloud Shell** (the `>_` icon in the portal's top bar; choose **Bash**).

## 1. Variables and providers

```bash
RG=financial-qa-rg
LOC=eastus2                      # pick a region where your chosen model is available
AOAI=fqa-openai-$RANDOM          # must be globally unique
ENVNAME=fqa-env
APP=financial-qa-bot
IMAGE=ghcr.io/aniketnandi/financial-qa-bot:latest

az extension add --name containerapp --upgrade
az provider register --namespace Microsoft.App --wait
az provider register --namespace Microsoft.OperationalInsights --wait
az provider register --namespace Microsoft.CognitiveServices --wait
az group create -n $RG -l $LOC
```

Cloud Shell variables are lost when the session times out. If that happens, re-run the variable lines, then set `AOAI` to the name the first run actually created.

## 2. Azure OpenAI resource and model deployment

```bash
az cognitiveservices account create -n $AOAI -g $RG -l $LOC \
  --kind OpenAI --sku S0 --custom-domain $AOAI

# See which chat models this region offers; pick a small, current one that supports tool calling
# (e.g. a "-mini" model) and note its name and version
az cognitiveservices account list-models -n $AOAI -g $RG \
  --query "[?capabilities.chatCompletion=='true'].{model:name, version:version}" -o table

MODEL=<model-name>               # from the table
VERSION=<model-version>          # from the table

# Deployment named "chat"; capacity 10 = 10K tokens/minute, which also caps spend
az cognitiveservices account deployment create -n $AOAI -g $RG \
  --deployment-name chat --model-name $MODEL --model-version $VERSION \
  --model-format OpenAI --sku-name GlobalStandard --sku-capacity 10

ENDPOINT=$(az cognitiveservices account show -n $AOAI -g $RG --query properties.endpoint -o tsv)
AOAI_KEY=$(az cognitiveservices account keys list -n $AOAI -g $RG --query key1 -o tsv)
```

If `GlobalStandard` is rejected in your region, try `--sku-name Standard`. You can also create the deployment in the Azure AI Foundry portal; either way, name it `chat`.

## 3. Container Apps environment and app

```bash
az containerapp env create -n $ENVNAME -g $RG -l $LOC

API_KEY=$(openssl rand -hex 16)
echo "Save this API key: $API_KEY"

az containerapp create -n $APP -g $RG --environment $ENVNAME \
  --image $IMAGE --target-port 8000 --ingress external \
  --cpu 1 --memory 2Gi --min-replicas 0 --max-replicas 1 \
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

From your own machine, in the project folder:

```bash
python evals/eval_qa.py --base-url <URL> --api-key <API_KEY> \
  --endpoint rag=/ask --golden evals/golden_set.jsonl --out evals/results_azure_rag --sleep 2
python evals/eval_qa.py --base-url <URL> --api-key <API_KEY> \
  --endpoint agent=/ask_agent --golden evals/golden_set.jsonl --out evals/results_azure_agent --sleep 2
```

Commit the two results folders. They are the Azure OpenAI numbers. The existing `results_rag/` and `results_agent/` folders are Gemini runs.

## 6. Updating after a code change

Push to `main`, wait for CI to publish the image, then roll a new revision with that commit's tag:

```bash
az containerapp update -n $APP -g $RG --image ghcr.io/aniketnandi/financial-qa-bot:<commit-sha>
```

## 7. Cost controls

- **Budget alert:** in the portal, go to **Cost Management → Budgets → Add**, for example $10/month with an email alert at 50%.
- **Rate cap:** the `--sku-capacity 10` deployment allows at most 10K tokens/minute. Each RAG call is roughly 2–3K tokens.
- **Scale to zero:** keep `--min-replicas 0`. A permanently warm replica removes cold starts, but it would use up a large share of the student credit each month.
- **Tear down everything:** `az group delete -n $RG --yes`

## Troubleshooting

| Symptom | Fix |
|---|---|
| Container stuck pulling the image / `unauthorized` | Make the GHCR package public (step 0) |
| `/ask` returns 502 | Check the deployment name is `chat`, and the endpoint and key secrets. View logs: `az containerapp logs show -n $APP -g $RG --follow` |
| 404 `DeploymentNotFound` | The model deployment is still provisioning; wait a minute |
| API version errors | Set `AZURE_OPENAI_API_VERSION` to a version your resource supports: `az containerapp update -n $APP -g $RG --set-env-vars AZURE_OPENAI_API_VERSION=<version>` |
| Out-of-memory restarts | `az containerapp update -n $APP -g $RG --cpu 2 --memory 4Gi` |

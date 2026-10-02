# CV OCR Service

A FastAPI microservice. It downloads CVs from a Google Shared Drive, runs PaddleOCR on them, and writes the results back to the drive.

For each CV `Jane_Doe.pdf` it writes:
- `Jane_Doe.ocr.txt`: the plain extracted text
- `Jane_Doe.ocr.json`: the text plus per-line bounding boxes and confidence scores

It accepts PDFs, images (PNG, JPEG, TIFF, BMP, WEBP, GIF) and native Google Docs, which it exports as PDF first.

## 1. Google setup (one time)

The service signs in as a regular Google user who already has access to the Shared Drive. It doesn't use a service account.

1. In [Google Cloud Console](https://console.cloud.google.com/), create or pick a project and **enable the Google Drive API**.
2. Open **Google Auth Platform → Branding** (older consoles call it the OAuth consent screen). Fill in the app name and support email, and set the **Audience** to **Internal**.
3. Open **Clients → Create client**, choose **Desktop app**, and copy the **Client ID** and **Client secret**.

Folder and file IDs come from the Drive URL: `https://drive.google.com/drive/folders/<FOLDER_ID>`.

## 2. Run on your server

```bash
cp .env.example .env        # set GOOGLE_OAUTH_CLIENT_ID/SECRET, API_KEY, OUTPUT_FOLDER_ID
docker compose build
docker compose run --rm cv-ocr python -m app.authorize   # one-time Google sign-in
docker compose up -d
docker compose logs -f
```

The sign-in command prints a link. Open it on any computer and sign in with an account that can edit the Shared Drive. After you approve, the browser lands on a `localhost` page that fails to load. Copy that page's full URL and paste it back into the terminal. The resulting token is stored in the `cv-ocr-data` Docker volume.

A service-account key or a gcloud credentials file still works too: put it in `./secrets/` and set `GOOGLE_CREDENTIALS_FILE=/secrets/<file>.json`.

The first build takes several minutes because it downloads Paddle and bakes the OCR models into the image. After that the container starts quickly and needs no internet access for OCR.

## 3. API

Interactive docs are at `http://<server>:8000/docs`. Every endpoint except `/health` requires the `X-API-Key` header when `API_KEY` is set.

### OCR a single CV (synchronous)
```bash
curl -X POST http://localhost:8000/ocr/file/<FILE_ID> \
  -H "X-API-Key: change-me" -H "Content-Type: application/json" \
  -d '{"output_folder_id": null, "include_lines": false}'
```
The response contains the full text, the text for each page, and links to the files it wrote to Drive.

### OCR a whole folder (background job)
```bash
curl -X POST http://localhost:8000/ocr/folder/<FOLDER_ID> \
  -H "X-API-Key: change-me" -H "Content-Type: application/json" -d '{"overwrite": false}'
# -> {"job_id": "...", "status": "queued", ...}

curl http://localhost:8000/jobs/<JOB_ID> -H "X-API-Key: change-me"
```
The job skips CVs that already have an `.ocr.txt` result unless you pass `"overwrite": true`. You can safely run it again, for example from cron.

### Output location
The service picks the output folder in this order:
1. `output_folder_id` in the request body
2. `OUTPUT_FOLDER_ID` in `.env`
3. the folder that contains the CV

## Configuration (`.env`)

| Var | Default | Notes |
|---|---|---|
| `GOOGLE_CREDENTIALS_FILE` | `/secrets/service-account.json` | path inside the container |
| `OUTPUT_FOLDER_ID` | *(empty)* | empty = write next to each CV |
| `OCR_LANG` | `en` | PaddleOCR language code; **rebuild** after changing it |
| `PDF_DPI` | `200` | higher is more accurate but slower |
| `MAX_PAGES` | `10` | pages OCR'd per file |
| `MAX_FILE_MB` | `25` | larger files are rejected |
| `API_KEY` | *(empty)* | empty disables auth; don't leave it empty on a public server |

## Notes
- **CPU only.** The service handles one OCR at a time and a one-page CV takes a few seconds. Requests arriving meanwhile wait in a queue. For more throughput, run more containers behind a load balancer.
- **Jobs are in memory.** Job status is lost on restart. The CVs already processed stay done, so you can just resend the folder request.
- **Word files (.docx) are not handled**, because OCR is for images. Convert them to PDF or Google Docs first.

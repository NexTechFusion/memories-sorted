---

## 🔴 Round 2: The "Upload Failure" Crisis Audit

**Participants:** Aris (UX), Kael (ML), Sloane (Ideas), Tess (QA)

**Tess (QA):** Let's be blunt—the upload is broken. I'm seeing multiple `422 Unprocessable Entity` and `500` errors. The `doUpload` logic in Alpine is trying to hit `/api/upload` but the backend signature has changed to expect `BackgroundTasks` and specific query params. If the job ID isn't returned exactly right, the whole frontend hangs in a "Sending..." state.

**Kael (ML):** My bad. I added `BackgroundTasks` to `api.py` but I didn't verify if the `python-multipart` dependency is fully handling the `file: UploadFile` alongside the new `context_type` and `context_id` query params. Also, the `syncer.sync()` call inside the background task is **too slow** and blocks the directory. If two photos upload at once, they both try to write to `index.json` simultaneously. Race condition city.

**Aris (UX):** From a user perspective, it’s even worse. If the upload fails, the progress bar just stays there forever. There's no "Retry" or "Clear" button. We need a fallback that doesn't just rely on a successful background job. If the job fails, the UI needs to snap back to idle safely.

**Sloane (Ideas):** We need a "Perfect Flow." 
1. **Frontend:** Immediate feedback. Show the image thumbnail *locally* before it even hits the server.
2. **Backend:** Receive file -> Save -> Return `202 Accepted` immediately. 
3. **Queue:** The AI pipeline should process 1-by-1, not all at once, to avoid CPU thrashing on this machine.

---

## 🛠️ The "Perfect Upload" Technical Spec

1.  **Frontend (Alpine.js):**
    - Use `fetch` instead of `XMLHttpRequest` for cleaner async/await.
    - Implement a `catch` block that resets `uploading = false` and flashes a real error message.
    - Provide a "local preview" thumb in the progress bento.

2.  **Backend (FastAPI):**
    - **Step 1:** Atomic save of the file to `/data/input`.
    - **Step 2:** Add to a persistent `QUEUE` (disk-backed).
    - **Step 3:** Return `job_id` and the filename immediately.
    - **Worker:** A single background loop that processes the queue sequentially to prevent `index.json` corruption.

3.  **Dependencies:** Ensure `python-multipart` is installed.

**Kael (ML):** I'll rewrite the API to handle the file first, task second.
**Aris (UX):** I'll design the "Error Recovery" UI.

**Dom, shall we execute this "Perfect Flow" rewrite?**

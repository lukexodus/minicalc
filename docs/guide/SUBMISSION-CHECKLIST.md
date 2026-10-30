# MiniCalc Final Submission Delivery Checklist

**Course:** CMPSC 132: Programming Languages (1st Semester, A.Y. 2025-2026)  
**Project:** MiniCalc Final Project Submission  
**Internal Target Time:** October 30, 2026, 12:00 (UTC+8)  
**Hard Submission Deadline:** October 30, 2026, 17:00 (UTC+8)  

> [!WARNING]
> **Strict Delivery Penalty:** The grading rubric penalizes late submissions by rubric band. Delivering just 1 hour late drops the score from Excellent (20 pts) to Good (15 pts). Two hours late drops to Satisfactory (10 pts), and beyond three hours drops to Unsatisfactory (5 pts). Complete all submission steps well before the 17:00 deadline!

---

## Submission Protocol & Task Ownership

All action items below must be executed in sequence. Owner assignments are to be filled in by the operator / group members.

| Step | Action Item | Target Time | Owner | Verification / Proof | Status |
| :---: | :--- | :---: | :---: | :--- | :---: |
| **1** | **Code Freeze & Version Tag** | 10:30 UTC+8 | *(blank)* | Ensure working tree is clean. Operator tags git release: `git tag -a v1.0.0 -m "release: MiniCalc v1.0.0"`. *(Note: Local coding agents do not create git tags).* | [ ] |
| **2** | **Generate & Verify Submission ZIP** | 11:00 UTC+8 | *(blank)* | Run `python scripts/make_submission.py --verify`. All 6 verification checks must report `[PASS]`. Verify ZIP size < 5 MB and confirm byte determinism across builds. | [ ] |
| **3** | **Google Drive Upload** | 11:30 UTC+8 | *(blank)* | Upload `dist/MiniCalc-CMPSC132-FinalProject.zip` to Google Drive into the project submission folder. | [ ] |
| **4** | **Configure Sharing Permissions** | 11:45 UTC+8 | *(blank)* | Right-click the uploaded ZIP on Google Drive $\to$ Share $\to$ General access $\to$ Set to **"Anyone with the link"** with role **"Viewer"**. Copy the shareable link. | [ ] |
| **5** | **Incognito Access & Download Test** | 12:00 UTC+8 | *(blank)* | Open a private/incognito browser window without any active Google account logins. Paste the Drive link. Confirm that the page loads, the file is visible, and clicking "Download" successfully retrieves the identical ZIP. Extract and test run `python -m minicalc -e "2+3*4"`. | [ ] |
| **6** | **Post Submission to MVLE Thread** | 12:30 UTC+8 | *(blank)* | Navigate to the official MVLE Course Final Project Submission Thread. Draft and post the group submission containing: (1) Group Member Names and Section, (2) Project Name (MiniCalc), (3) Brief project description, and (4) The verified public Google Drive link. | [ ] |
| **7** | **Timestamped Screenshot Capture** | 12:45 UTC+8 | *(blank)* | Take a full-screen screenshot of the posted submission message in the MVLE thread, ensuring the post content, system clock, date, and submission timestamp are clearly visible. Archive the screenshot in group records. | [ ] |
| **8** | **Final Team Sign-Off** | 13:00 UTC+8 | *(blank)* | All group members independently access the posted MVLE link, download the ZIP, and sign off that delivery is complete and accessible prior to the 17:00 hard cutoff. | [ ] |

---

## Detailed Step-by-Step Instructions

### Step 1: Code Freeze & Tagging (Operator Only)
1. Verify master branch has all tasks (`DOC-001`, `DOC-002`, `DOC-003`) merged.
2. Confirm `git status` reports working tree clean.
3. Operator tags the release:
   ```bash
   git tag -a v1.0.0 -m "release: MiniCalc v1.0.0"
   ```

### Step 2: Build and Verify Submission
Execute the automated submission packager and test runner:
```bash
python scripts/make_submission.py --verify
```
Confirm the following output appears without failure:
- `[PASS] pytest -q passed`
- `[PASS] python scripts/check_docs.py passed`
- `[PASS] minicalc -e '2+3*4' returned expected '= 14'`
- `[PASS] minicalc examples/01_basics.mc exited with 0`
- `[PASS] minicalc examples/05_errors.mc exited with 1`
- `[PASS] Shipped markdown files contain no excluded path references`

Verify the archive manifest:
```bash
python scripts/make_submission.py --list
```
Confirm that no internal governance files (`.git`, `patch/`, `docs/reports`, `docs/decisions`, `docs/tasks`, `docs/prompts`, `docs/guide`, `scripts/make_submission.py`, `tests/test_make_submission.py`) are present in the manifest.

### Step 3: Google Drive Upload
1. Open Google Drive in your web browser.
2. Navigate to your academic submissions directory.
3. Upload `dist/MiniCalc-CMPSC132-FinalProject.zip`.

### Step 4: Configure Public Viewing Access
1. Select the uploaded ZIP file.
2. Click **Share** (or right-click $\to$ Share).
3. Under **General access**, select **Anyone with the link**.
4. Set the permission role to **Viewer**.
5. Click **Copy link** and save it to your clipboard.

### Step 5: Incognito Verification
1. Launch a new Incognito / Private browsing window (ensuring no Google session is authenticated).
2. Paste the copied link into the address bar and press Enter.
3. Verify that the file preview appears without prompting for login or permission requests.
4. Click **Download**, save the ZIP to disk, and extract it to confirm archive integrity.

### Step 6: Post to MVLE Final Project Thread
1. Log in to the Course MVLE portal.
2. Navigate to the **Final Project Submission Thread**.
3. Create a reply with the following format:
   ```text
   Course: CMPSC 132 (1st Sem, A.Y. 2025-2026)
   Project Title: MiniCalc — Verified 32-Bit Arithmetic Programming Language
   Group Members:
     - Adrian Luke A. Labasan
     - Alejandrei Jazz F. Lopez
     - Geila May C. Rigayen
     - Melvie Jeanna O. Abad
   
   Google Drive Link (Public View):
   [PASTE LINK HERE]
   
   Notes: ZIP contains full source code, test suite, examples, and documentation.
   ```
4. Click **Submit Post**.

### Step 7: Timestamped Proof Capture
1. After posting, locate your post in the forum thread.
2. Capture a full-screen screenshot that shows:
   - The thread name and post content.
   - The timestamp of the post.
   - The system clock showing date and time (prior to Oct 30, 17:00 UTC+8).
3. Save the image file as proof of on-time delivery.

### Step 8: Final Team Sign-Off
Each group member downloads the package from the link posted in MVLE and verifies:
- File extracts cleanly.
- `python main.py -e "2+3*4"` outputs `= 14`.
- All members confirm completion.

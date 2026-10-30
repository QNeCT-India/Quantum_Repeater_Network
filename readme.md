# Git Usage

You can run these directly in **PowerShell**, **CMD**, or **terminal** inside your project folder.

```bash
# 1. Go to your project directory
cd "D:\Research\Quantum_Library"

# 2. Initialize a git repository (if not already)
git init

# 3. Add your remote GitHub repo (change URL)
git remote add origin https://github.com/USERNAME/REPOSITORY_NAME.git

# 4. Add all project files
git add .

# 5. Commit with a message
git commit -m "Initial commit: upload quantum library"

# 6. Push to the main branch
git branch -M main
git push -u origin main
```

- If you already have an initialized git repo and just want to push updates:

  ```bash
  git add .
  git commit -m "Update library"
  git push
  ```

- Check the commit history of your current Git repository

  ```bash
  git log
  ```

- To see what's already set:

  ```bash
  git remote -v
  ```

  It'll output something like:

  ```text
  origin  https://github.com/OldRepoName.git (fetch)
  origin  https://github.com/OldRepoName.git (push)
  ```

- Module has been pushed to github. Now I want to make some changes and push the module again. What are the steps for that?

  1. Go to your project folder

     ```bash
     cd "D:\Research\Quantum Repeaters\QRN_Code"
     ```

  2. Check current branch

     ```bash
     git branch
     ```

     If it shows `* main`, you're good.

     ```bash
     git checkout main
     ```

  3. Pull the latest changes

     ```bash
     git pull origin main
     ```

  4. Make your code changes

  5. Add all changed files

     ```bash
     git add .
     ```

  6. Commit the changes

     ```bash
     git commit -m "Updated quantum library with bug fixes and new features"
     ```

  7. Push to GitHub

     ```bash
     git push origin main
     ```


- Create new directory:

  **For multiple folders**: Separate the names with spaces: `mkdir folder1 folder2 folder3`.

  **For nested folders**: Use the `-p` flag on Linux/macOS to create a path of folders all at once (e.g., `mkdir -p parent/child/grandchild`).

  **For names with spaces**: Enclose the name in quotation marks (e.g., `mkdir "my new folder"`).

- Delete directory:

  | Type | Command | Effect |
  |--|--|--|
  | **Non-empty** | `rm -r folder_name` | Deletes everything recursively. |
  | **Empty** | `rmdir folder_name` | Safely removes empty folders only. |
  | **Protected / Stubborn** | `rm -rf folder_name` | Forces deletion without prompting. |



# BRANCH

- Check which branch you are working in.

  ```bash
  git branch
  ```

- Create new branch

  ```bash
  git branch <branch-name>
  git switch <branch-name>
  ```

# Create Environment

- How to create a virtual environment?

  **Step 1: Go to your project folder**

  ```bash
  cd ~/Documents
  ```

  **Step 2: Create the virtual environment**

  Run:

  ```bash
  python3 -m venv venv
  ```

  This creates a folder named `venv` inside your project.

  You can use any name instead of `venv`:

  ```bash
  python3 -m venv myenv
  ```

  **Step 3: Activate the virtual environment**

  ```bash
  source venv/bin/activate
  ```

  **Step 4: Install packages inside the venv**

  ```bash
  pip install numpy matplotlib qiskit
  ```

  **Step 5: Save installed packages (recommended)**

  ```bash
  pip freeze > requirements.txt
  ```

  **Step 6: Exit the virtual environment**

  ```bash
  deactivate
  ```

- Suppose running a .py file after the venv is created then use:

  ```bash
  python3 /home/ss-iiserm/Documents/VQB_code.py
  ```

```bash
python -m venv env
```

- See total virtual environments you have created in your system:

  ```bash
  ls ~/venvs
  ```



- Open GUI

  ```bash
  streamlit run gui_app/app.py
  ```
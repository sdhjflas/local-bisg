# Setting Up BISG Label Generator on New Laptop

Quick guide to get the label generator running on your new Windows laptop.

## Step 1: Install Python

1. Go to https://www.python.org/downloads/
2. Download Python 3.9 or higher
3. Run the installer
4. ⚠️ **IMPORTANT**: Check the box "Add Python to PATH"
5. Click "Install Now"

## Step 2: Clone the Repository

Open Command Prompt and run:

```batch
cd Documents
git clone https://github.com/sdhjflas/local-bisg.git
cd local-bisg
git checkout claude/local-label-maker-01JR9CwSVA4HVhWNA5K3fMZC
```

If git isn't installed, download it from: https://git-scm.com/download/win

## Step 3: Install Dependencies

```batch
py -m pip install -r requirements_local.txt
```

## Step 4: Test Run

```batch
py local_app.py
```

Open your browser to: http://localhost:5000

If it works, you're ready to create the desktop app!

## Step 5: Create Desktop App (see TASKBAR_APP.md)

Follow the instructions in `TASKBAR_APP.md` to:
- Create a launcher with an icon
- Pin it to your taskbar
- Run it like any other app

---

## Troubleshooting

### Python not found
- Make sure you checked "Add Python to PATH" during installation
- Try using `py` instead of `python`
- Restart Command Prompt after installing Python

### Git not found
- Install Git from: https://git-scm.com/download/win
- Restart Command Prompt after installation

### Port 5000 already in use
- Change the port in the launcher: `set PORT=5001`

### Dependencies won't install
- Upgrade pip first: `py -m pip install --upgrade pip`
- Try again: `py -m pip install -r requirements_local.txt`

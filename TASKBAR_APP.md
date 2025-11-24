# Create a Taskbar App for BISG Label Generator

Turn the label generator into a one-click app on your Windows taskbar!

## Quick Setup (5 minutes)

### Step 1: Create the Icon

**Option A: Use the provided SVG (recommended)**

1. Go to https://convertio.co/svg-ico/ (or any SVG to ICO converter)
2. Upload `label_icon.svg` from this folder
3. Convert to ICO format
4. Download as `label_maker.ico`
5. Save it in the `local-bisg` folder

**Option B: Use a different icon**

1. Find any icon you like (search "barcode icon" or "label icon")
2. Convert it to `.ico` format using an online converter
3. Save as `label_maker.ico` in the `local-bisg` folder

**Option C: Skip the custom icon**

- Windows will use a default icon (still works fine!)

---

### Step 2: Create Desktop Shortcut

1. **Right-click** on `Launch_Label_Maker.bat`
2. Select **"Create shortcut"**
3. Right-click the new shortcut
4. Select **"Properties"**
5. In the **"Shortcut"** tab:
   - Click **"Change Icon"**
   - Click **"Browse"**
   - Select `label_maker.ico` (if you created it)
   - Click **OK**
6. Change the name to: **"BISG Label Generator"**
7. Click **Apply**, then **OK**

---

### Step 3: Pin to Taskbar

**Method 1: From Desktop**
1. Right-click the shortcut you just created
2. Select **"Pin to taskbar"**
3. Done! ✅

**Method 2: From File Explorer**
1. Open the `local-bisg` folder
2. Right-click `Launch_Label_Maker.bat`
3. Select **"Pin to taskbar"**
4. Right-click the taskbar icon
5. Right-click **"Launch_Label_Maker"** in the jump list
6. Select **"Properties"**
7. Change the icon (see Step 2 above)

---

### Step 4: Test It

1. Click the icon in your taskbar
2. A command prompt window should open briefly
3. Your browser should open to the label generator
4. Start making labels!

---

## How It Works

When you click the taskbar icon:

1. ✅ Opens a command window (you can minimize this)
2. ✅ Starts the Flask server automatically
3. ✅ Opens your default browser to http://localhost:5000
4. ✅ Ready to generate labels!

To stop the server:
- Close the command prompt window
- Or press `Ctrl+C` in the command prompt

---

## Advanced: Hide the Command Window

If you don't want to see the command prompt window at all, create a VBS launcher:

1. Create a new file: `Launch_Label_Maker.vbs`
2. Add this code:

```vbscript
Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
WshShell.Run "Launch_Label_Maker.bat", 0, False
Set WshShell = Nothing
```

3. Create a shortcut to the `.vbs` file instead of the `.bat` file
4. Add your icon to the shortcut
5. Pin that to the taskbar

Now it runs completely in the background! The browser will open but no command window.

---

## Troubleshooting

### Icon doesn't show up
- Make sure `label_maker.ico` is in the same folder as the batch file
- Try logging out and back in to Windows
- Try unpinning and re-pinning to taskbar

### Browser doesn't open automatically
- Wait a few seconds after clicking the icon
- Manually open: http://localhost:5000
- Check if port 5000 is in use (change PORT in the batch file)

### App won't start
- Make sure Python is installed: `py --version`
- Make sure dependencies are installed: `py -m pip install -r requirements_local.txt`
- Check the command prompt window for errors

### Multiple instances running
- Only click the icon once
- Close the command prompt window to stop the server
- Check Task Manager for multiple Python processes

---

## Customization

### Change the Port

Edit `Launch_Label_Maker.bat` and change:
```batch
set PORT=5000
```
to:
```batch
set PORT=5001
```
(or any other port number)

### Auto-start on Login

1. Press `Win + R`
2. Type: `shell:startup`
3. Press Enter
4. Copy your shortcut to this folder
5. The label generator will start automatically when you log in

---

## Uninstalling

To remove from taskbar:
1. Right-click the taskbar icon
2. Select "Unpin from taskbar"

To completely remove:
1. Delete the `local-bisg` folder
2. Uninstall Python (optional)

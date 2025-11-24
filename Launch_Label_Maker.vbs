' BISG Label Generator - Silent Launcher
' This launches the app without showing a command window

Set WshShell = CreateObject("WScript.Shell")

' Change to script directory
WshShell.CurrentDirectory = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)

' Run the batch file hidden (0 = hidden, False = don't wait)
WshShell.Run "Launch_Label_Maker.bat", 0, False

Set WshShell = Nothing

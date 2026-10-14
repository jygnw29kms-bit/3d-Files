Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
shell.Run "pythonw.exe " & Chr(34) & folder & "\camera_control.py" & Chr(34) & " off", 0, False

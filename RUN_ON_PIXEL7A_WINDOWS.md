# Run Ingridio on Pixel 7a (Windows, USB, Terminal Only)

This guide uses command line only (no Android Studio UI launch).

## 1) Phone setup (one-time)

1. Open Settings > About phone.
2. Tap Build number 7 times.
3. Enter your PIN.
4. Go to Settings > System > Developer options.
5. Turn on USB debugging.
6. Connect phone with a data USB cable.
7. On the popup, tap Allow and enable Always allow from this computer.

## 2) PC setup (per terminal session)

Open Command Prompt in project folder and run:

    cd C:\Users\DELL\Desktop\Ingridio\Ingridio
    set PATH=%PATH%;C:\Users\DELL\AppData\Local\Android\sdk\platform-tools

Optional permanent PATH (run once in Command Prompt):

    setx PATH "%PATH%;C:\Users\DELL\AppData\Local\Android\sdk\platform-tools"

Then close and reopen terminal.

## 3) Verify device connection

    adb kill-server
    adb start-server
    adb devices -l

Expected:
- Your Pixel appears with status: device

If status is unauthorized:
- Unlock phone and accept USB debugging popup.

If no device appears:
- Change USB mode to File Transfer.
- Try a different cable/USB port.
- Reconnect and run adb devices -l again.

## 4) Run app on Pixel 7a

From project root:

    flutter pub get
    flutter devices
    flutter run -d 33221JEHN06539

If your device id changes, use the id shown by flutter devices.

## 5) Smoothness/performance check

For realistic UI smoothness testing on phone:

    flutter run --profile -d 33221JEHN06539

## 6) Useful during development

In the flutter run terminal:
- Press r for hot reload
- Press R for hot restart
- Press q to quit

## 7) Troubleshooting quick commands

    flutter doctor -v
    adb devices -l
    flutter devices

If adb command is not found, re-run PATH command from step 2.

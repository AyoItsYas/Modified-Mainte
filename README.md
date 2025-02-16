# Mainte

https://github.com/user-attachments/assets/8ab0e6b1-4cc9-47fa-a48c-478465b420b0

https://github.com/user-attachments/assets/f1fd1d4a-e637-4057-9b21-d2a3caa7d337

https://github.com/user-attachments/assets/310605ea-8d2e-4de6-80ed-95abcd4e8244

- Designed screen resolution is 1920x1080
- There is a lot of binanries/tools that are not mentioned here that should be available on most distributions of linux, these are the notable exceptions.

  ```
  vnstat       : Network usage statistics
  python3      : For text formatting with complex logic
  playerctl    : Media playback status and metadata
  radeontop    : AMD GPU statistics
  bluetoothctl : Bluetooth device status
  adb          : Android device connection status
  usbguard     : Rules to govern secure USB connections
  xdotool      : To identify window/app names from web shortcut apps (Media playback)
  acpi         : Battery status
  hwinfo       : Hardware information
  bc           : For floating point arithmetic
  ```

# Setting Up

- Clone the repo to a desired location and run conky on all the overlays. You can use conky manager or any tool to manage the theme, or [this](https://github.com/AyoItsYas/bin/blob/main/conkyd) simple script should suffice. How you set it up is upto you, I recommend to place the script on your `PATH` and use it as a tool to manage conky themes in general.

  ```
  git clone https://github.com/AyoItsYas/Mainte.git
  mkdir -p ~/.conky/
  mv ./Mainte/ ~/.conky/

  curl https://raw.githubusercontent.com/AyoItsYas/bin/main/conkyd > conkyd
  chmod +x conkyd
  ./conkyd start
  ```

- For the weather overlay to work you need an API key from https://openweathermap.org/. Configure the enviornment variable `OPENWEATHERMAP_API_KEY` with the value.

  ```
  echo 'export OPENWEATHERMAP_API_KEY="your_api_key"' >> ~/.bashrc
  ```

# Contributing

Anyone is welcome to contribute to this project. If you have any ideas or suggestions, feel free to open an issue or a pull request. If you want to add a new overlay, please follow the existing structure.

- [ ] An installer script to setup the theme and the dependencies

<div align="center">
  <br/>
  <a href="https://www.buymeacoffee.com/ayoitsyas">
    <img src="https://img.buymeacoffee.com/button-api/?text=Buy me a coffee&emoji=☕&slug=ayoitsyas&button_colour=FFDD00&font_colour=000000&font_family=Poppins&outline_colour=000000&coffee_colour=ffffff" />
  </a>
</div>

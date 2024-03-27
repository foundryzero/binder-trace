<p align="center">
  <img src="https://github.com/foundryzero/binder-trace/raw/main/binder-trace.png" alt="binder-trace logo"/>
</p>

# Binder Trace

Binder Trace is a tool for intercepting and parsing Android Binder messages. Think of it as "Wireshark for Binder".

![binder-trace demo](https://github.com/foundryzero/binder-trace/raw/main/binder-trace.gif)




# Requirements

python version >= 3.9


# ⚙️ Installation

You'll need a rooted Android device or emulator.

* (Linux only) - install xclip or xsel for "copy to clipboard" functionality
    > `sudo apt-get install xclip`
    >
    > `sudo apt-get install xsel`

* Install from PyPi 
    > `pip install binder-trace`

* Check which version of frida is installed (make sure you've pip installed the requirements)
    > `pip list | grep frida`
* Download the matching version of frida-server from the [frida releases page](https://github.com/frida/frida/releases)
* Make sure adb is running as root, push frida-server to your device and run it
    > `adb root`
    > 
    > `adb push frida-server /data/local/tmp`
    >
    > `adb shell`
    >
    > `chmod u+x /data/local/tmp/frida-server`
    >
    > `adb shell /data/local/tmp/frida-server`
 

# Arguments

| Argument                | Description                                                                                                                           |
|-------------------------|---------------------------------------------------------------------------------------------------------------------------------------|
| -h                      | Prints the argument help.                                                                                                             |
| -d&nbsp;DEVICE          | The device to attach to e.g. "emulator-5554". Use `adb devices` to list available devices. If not provided defaults to the USB device. |
| -p&nbsp;PID             | The pid of the process on DEVICE to attach to.                                                                                        |
| -n&nbsp;NAME            | The name of the process on DEVICE to attach to e.g. "Messaging".                                                                      |
| -P&nbsp;PACAKAGENAME    | The packagename of the application on DEVICE to spawn to e.g. "Messaging".                                                            |
| -a&nbsp;[9, 10, 11, 13] | The version of android to load structures for.                                                                                        |
| -s&nbsp;STRUCTPATH      | The path to the directory of structure files.                                                                                         |
| -c&nbsp;CONFIG          | The path to the config file to filter.                                                                                                |

# ▶️ Starting binder trace

To start binder trace we need to pick a device and process to attach to. 
In the following example we use `adb` and `frida-ps` to identify a process to attach to on a local emulator. As it's an Android 11 emulator we choose the Android 11 structs directory. Pick the struct directory that most closely matches your version of Android. If you would like structures for a different version of Android, please let us know. Once it's running start using the target app to generate some binder transactions. 

```
> adb devices
List of devices attached
emulator-5554   device

> frida-ps -Ua
 PID  Name           Identifier
----  -------------  ----------------------------
8334  Messaging      com.android.messaging
7941  Phone          com.android.dialer
9607  Settings       com.android.settings

> cd binder_trace
> binder-trace -d emulator-5554 -n Messaging -a 11
```

# ⌨️ Controls

## 🌐 Global 
| Key              | Action                                 |
|------------------|----------------------------------------|
| `up`             | Move up                                |
| `down`           | Move down                              |
| `shift + up`     | Page up                                |
| `shift + down`   | Page down                              |
| `home`           | Go to top                              |
| `end`            | Go to bottom                           |
| `tab`            | Next pane                              |
| `shift + tab`    | Previous pane                          |
| `ctrl + c`       | Copy pane to clipboard                 |
| `space`          | Pause/Unpause transaction recording    |
| `c`              | Clear                                  |
| `h`              | Open help                              |
| `r`              | Reload config file                     |
| `q`              | Quit                                   |

## 📈 Frequency pane
| Key              | Action                                 |
|------------------|----------------------------------------|
| `p`           |   Toggle order asc/desc                   |
| `w`           |   Jump to next interface                  |
| `s`           |   Jump to previous interface              |
| `a`           |   Toggle all filters on                   |
| `n`           |   Toggle all filters off                  |
| `enter`       |   Toggle Filter                           |

# 🔎 Config File
To filter define any or all of the interface, method, type and inclusive options. To not use an option leave it blank `""`

## Without -c argument

```
> binder-trace -d emulator-5554 -n Contacts -a 13
```
![Before Config](https://github.com/foundryzero/binder-trace/raw/main/binder-trace-before-config.png)

## With -c argument
### config.json
```py
{
    "filters": [
        {
            "interface": "android.gui.IDisplayEventConnection",
            "method": "requestNextVsync",
            "type": "",
            "inclusive": false
        },
        {
            "interface": "android.content.IContentProvider",
            "method": "",
            "type": "call",
            "inclusive": false
        }
    ]
}
```

```
> binder-trace -d emulator-5554 -n Contacts -a 13 -c .\binder_trace\binder_trace\config.json
```

`android.gui.IDisplayEventConnection`->`requestNextVsync`->`""` and `android.content.IContentProvider`->`""` ->`call` have been filtered out

![After Config](https://github.com/foundryzero/binder-trace/raw/main/binder-trace-after-config.png)

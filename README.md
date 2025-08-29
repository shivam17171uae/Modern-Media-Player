# All Player 🎵🎬🖼️

![App Screenshot](https://i.imgur.com/your-screenshot-url.png)
_**Note:** You should take a screenshot of your running application, upload it to a site like [Imgur](https://imgur.com/upload), and replace the link above with your image URL._

A modern, sleek media player for music, video, and pictures, built with Python. This application features a dark-themed, intuitive UI powered by CustomTkinter and a robust playback engine using `python-vlc`.

## ✨ Features

- **All-in-One Library:** Manage your music, videos, and pictures in one place with separate, organized tabs.
- **Modern Interface:** A beautiful, dark-themed UI built with CustomTkinter that looks great on any modern OS.
- **High-Quality Playback:** Powered by the robust VLC engine, ensuring compatibility with a wide range of media formats.
- **Persistent Libraries:** Your media libraries are saved locally in JSON files, so they persist between sessions.
- **Album Art Display:** Automatically extracts and displays album art for music tracks, including a stunning blurred-backdrop effect that fills the window.
- **Full Playback Controls:** Includes all essential controls:
    - Play, Pause, Next, and Previous
    - Interactive seekable progress bar
    - Volume slider and mute button
    - Shuffle and Repeat (Off, Repeat All, Repeat One)
- **Search Functionality:** Instantly filter your media library in real-time within each tab.
- **Dynamic & Responsive:** The UI elements, including the blurred music background, resize and adapt to changes in the window size.

## 🛠️ Prerequisites

Before you can run this project, you will need the following installed on your system:

1.  **Python:** Version 3.10 or newer is recommended.
2.  **VLC Media Player:** The `python-vlc` library is a wrapper around the actual VLC application. You **must** have VLC Media Player installed.
    - [Download VLC Media Player](https://www.videolan.org/vlc/)
3.  **Git:** To clone the repository.

## ⚙️ Installation & Setup

Follow these steps to get the project running on your local machine.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YOUR_USERNAME/Modern-Media-Player.git
    cd Modern-Media-Player
    ```
    *(Replace `YOUR_USERNAME` with your actual GitHub username)*

2.  **Create a `requirements.txt` file:**
    In the root of the project, create a file named `requirements.txt` and add the following lines:
    ```
    customtkinter
    Pillow
    python-vlc
    tinytag
    ```

3.  **Install Python packages:**
    It's highly recommended to use a virtual environment.
    ```bash
    # Create and activate a virtual environment (optional but good practice)
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    # Install the required libraries
    pip install -r requirements.txt
    ```

## ▶️ How to Run

Once the setup is complete, you can run the application with the following command:

```bash
python main.py

Click "Add Files" in any tab to start building your media library!

📄 License
This project is licensed under the MIT License. See the LICENSE file for details.
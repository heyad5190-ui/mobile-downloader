name: Build Android APK

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-22.04

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'

    - name: Setup Java JDK
      uses: actions/setup-java@v4
      with:
        distribution: 'temurin'
        java-version: '17'

    - name: Setup Android SDK & Accept Licenses
      uses: android-actions/setup-android@v3

    - name: Install System Dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y build-essential ccache git libffi-dev libssl-dev python3-dev zip unzip ffmpeg autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libreadline-dev libgdbm-dev libsqlite3-dev libdb5.3-dev libbz2-dev libexpat1-dev liblzma-dev wget curl
        pip install --upgrade pip
        pip install "cython<3.0.0" buildozer setuptools

    - name: Link Licenses to Buildozer and Build
      run: |
        yes | sdkmanager --licenses || true
        mkdir -p ~/.buildozer/android/platform/android-sdk/licenses
        cp -r $ANDROID_HOME/licenses/* ~/.buildozer/android/platform/android-sdk/licenses/ || true
        buildozer -v android debug

    - name: Upload APK Artifact
      uses: actions/upload-artifact@v4
      with:
        name: python-app-apk
        path: bin/*.apk

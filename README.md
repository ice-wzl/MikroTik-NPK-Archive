# MikroTik-NPK-Archive
## ⚠️⚠️⚠️ The Firmware has moved ⚠️⚠️⚠️
- After adding in some new firmware this repo is simply growing too large. I have decided to stand up all the firmware on a web server: http://npk-archive.space
- Firmware is up to date as of 2/11/25. With the move to a VPS, I have gained the ability to update the firmware more often as new MikroTik releases come out
- I am planning to write a very simple front end for this site in the future, for now you will have to endure with a simple nginx offering.
## Why this repo
- After the Margin Research findings were published about MikroTik routers, the company removed all download links to their older firmware. The only versions available for download are those that are not vulnerable to the Margin Research exploit. Historically, MikroTik has been very unfriendly to security researchers and jailbreaks of their routers. They go to great lengths to ensure little is known about how these devices actually function. Most of the public information regarding MikroTik internals come from security researches like Margin Research https://margin.re/pulling-mikrotik-into-the-limelight-2/, and Jacob Baines https://github.com/jacob-baines.

## Inspiration 
- As a researcher myself, I often want to download an older firmware image to flash onto a device, however finding older .npk files is increasingly difficult as the years progress. A Reddit user smileymattj realized that MikroTik didnt actually remove the old .npk files from their website, they simply removed the download link to them. Thus, if you were to take a download link to a new version and swap out the newer version with an older one you could download the older .npk https://www.reddit.com/r/mikrotik/comments/1dfvguh/archive_of_routeros_versions/
- MikroTik had a few variations in their URL scheme depending on what branch you were pulling from (stable, long-term, development, testing), however with a bit of massaging I was able to figure out their url schemes. They additionally used a slightly different url for their x86 .npk files.

## Are the backdoored?
- Short answer no. MikroTik makes it very difficult to backdoor their .npk files as Margin Research explains https://margin.re/pulling-mikrotik-into-the-limelight-2/.
- Additionally I am releasing the tool I used to pull their repo of .npk files. If you want to check if an .npk in this repo is backdoored simply use the tool to pull the identical version and compare SHA-256 hashes :)

## How do I use the download tool?
- Its pretty simple it has two modes of operation, either pull all version from a particular branch, or pull one version.
````
python3 npk_downloader.py --help
usage: npk_downloader.py [-h] [-a | -s]

options:
  -h, --help    show this help message and exit
  -a, --all     Download all .npk files from a specific branch
  -s, --single  Download single .npk file from a branch
````
### Single Version 
- Simply pick the branch, version and architecture you wish to pull. I have built out the valid versoin from the MikroTik changelogs.
````
python3 npk_downloader.py -s
Downloading single .npk file from True
1 arm
2 arm64
3 mipsbe
4 mmips
5 smips
6 tile
7 ppc
8 x86
[+] Select your arch: 1
1 Long-term release tree
2 Stable release tree
3 Testing release tree
4 Development release tree
[+] Select your branch: 1
[+] Type the version you want
6.49.10, 6.49.8, 6.48.7, 6.48.6, 6.48.5, 6.47.10, 6.47.9, 6.46.8, 6.46.7, 6.45.9, 6.45.8, 6.44.6, 6.44.5, 6.43.16, 6.43.15, 6.43.14, 6.43.13, 6.42.12, 6.42.11, 6.42.10, 6.42.9, 6.40.9, 6.40.8, 6.40.7, 6.40.6, 6.39.3, 6.38.7, 6.37.5, 6.37.4, 6.34.6, 6.34.5, 6.32.4, 6.32.3, 6.30.4, 6.30.2, 6.30.1
>>> 6.48.6 
[+] Target url:
https://download.mikrotik.com/routeros/6.48.6/routeros-arm-6.48.6.npk
[+] Status Code: 200

╰─⠠⠵ ls *.npk
routeros-arm-6.48.6.npk
````
### Pull All
- Simply run the tool with the `-a` option and select the branch you wish to rip. Again the valid version were built from the MikroTik changelogs.
````
python3 npk_downloader.py -a
1 Long-term release tree
2 Stable release tree
3 Testing release tree
4 Development release tree
[+] Select your branch: 2
````
## What do I do with an .npk file
- The easiest way to examine the firmware is to dump it with `binwalk`
- Simply run `binwalk -e routeros.npk`
- This command will extract the filesystem and you will have access to the MikroTik binaries for security research.

## If you find a version missing
- If you find a version missing, please let me know with the Pull Request, and I will do my best to find it for you!


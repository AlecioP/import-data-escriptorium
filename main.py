import time
import re
import json
import pyautogui
import pyperclip
from pathlib import Path

from argparse import ArgumentParser

parser = ArgumentParser(description="Automatic import of data into escriptorium")

parser.add_argument("--import_folder",type=str,help="Path to root directory of data to import",nargs=1,required=True)

ARGS = parser.parse_args()

IMPORT_FOLDER = ARGS.import_folder[0]

IMAGES_DIR = "./screenshots/"

FACTOR = 1


def clickImage(IMG,CONF : float,GREY=False,CLICK_N=1):
	# 4 element tuple
	toFind = IMAGES_DIR+IMG
	location = pyautogui.locateOnScreen(toFind,grayscale=GREY)
	x,y = pyautogui.center(location)
	pyautogui.click(x/FACTOR,y/FACTOR,clicks=CLICK_N,interval=1)
	return (x,y)

def chrome_url_bar():
    pyautogui.hotkey("alt","d")
    return
    find1 = IMAGES_DIR + "chrome_info.png"
    find2 = IMAGES_DIR + "chrome_star.png"
    loc1 = pyautogui.locateOnScreen(find1)
    loc2 = pyautogui.locateOnScreen(find2)
    click_x = loc1.left + loc1.width ((loc2.left - (loc1.left + loc1.width))/2 )
    click_y = loc1.top + (loc1.height/2)
    pyautogui.click(click_x,click_y,clicks=1,interval=1)


# FOR EACH FOLDER IN ROOT 

MAP_JSON_PATH = "./folder_to_url.json"
MAP_FOLDER_TO_ESCR_DOC = {}
if Path(MAP_JSON_PATH).exists():
    with open(Path(MAP_JSON_PATH),"r") as fd:
        MAP_FOLDER_TO_ESCR_DOC = json.load(fd)


Path("QUEUE_DONE.txt").touch(exist_ok=True)

print("Giving you time to setup the windows. Make sure escriptorium project's browser window is visible on the screen")
time.sleep(5)
try:
    for f in Path(IMPORT_FOLDER).glob("*/"):
        # ENTER ONE
        DOC_ID = list(f.glob("*/"))[0].parts[-1]
        # GET DOC ID
        print(DOC_ID)
        #print(f)
        #print((f / DOC_ID).resolve())

        with open("QUEUE_DONE.txt","r") as fd:
            if DOC_ID in fd.read():
                print(f"Skip cause DOC_ID={DOC_ID} has already been imported")
                continue

        # paste all names of images each surrounded by double quotes
        files_string  = ""
        images = list( [i for format in ["jpg","jpeg","png"] for i in (f / DOC_ID).glob(f"*.{format}")] )
        # pathlib.glob does not expand brace expansion so alternative is the one above
        # images = (f / DOC_ID).glob("*.{jpg,jpeg,png}")
        for img in images:
            print(img)
            files_string = f"{files_string} \"{img.name}\""

        if len(files_string) > 250:
            count = 1
            for img in images:
                new_stem = f"{DOC_ID}_{count:03}i"
                files_string = files_string.replace(img.stem,new_stem)
                img.rename(img.with_stem(new_stem))
                # Also need to rename transcription if present
                for f1 in (f / DOC_ID).glob("*/"):
                    if f1.parts[-1] == "page" :
                        with open((f1 / (img.stem + ".xml") ),"rw") as fd:
                            new_content = fd.read().replace((img.stem,new_stem))
                            fd.write(new_content)
                        (f1 / (img.stem + ".xml")).rename(f1 / (new_stem + ".xml"))
                count += 1 

        if len(files_string) > 250:
            print("SKIP because filenames string is too long after renaming")
            continue

        # TODO (optional) undo renaming after import

        # click "create document" button
        clickImage("create_document.png",CONF=0.9,CLICK_N=2)
        # enter DOC ID
        clickImage("name.png",CONF=0.9)
        pyautogui.write(DOC_ID)
        # click "----------" 
        clickImage("dots.png",CONF=0.9)
        # type latin
        pyautogui.write("latin")
        # click "Latin" screenshot
        clickImage("latin.png",CONF=0.9)
        # click create button
        clickImage("ok_create.png",CONF=0.9)
        # MACRO click url bar
        chrome_url_bar()
        #Copy to clipboard to get Doc ID in escriptorium
        pyautogui.hotkey('ctrl','c') 
        time.sleep(1)
        MAP_FOLDER_TO_ESCR_DOC[str((f  / DOC_ID).resolve())] = pyperclip.paste()
        # arrow right
        pyautogui.press("right")
        # delete 5 chars (edit/) 
        keys_sequence = []
        for times in range(0,len("edit/")):
            keys_sequence.append("backspace")
        pyautogui.press(keys_sequence,interval=1)
        # type "images"
        pyautogui.write("images")
        pyautogui.press("enter")
        # Wait to load 1 second
        time.sleep(1)
        # click "upload" screenshot
        RETRY = 0
        while True:
            try:
                clickImage("upload.png",CONF=0.9)
                break
            except pyautogui.ImageNotFoundException:
                RETRY += 1
                if RETRY > 3:
                    break

        # MACRO click explorer address bar
        pyautogui.press("f4")
        pyautogui.hotkey("ctrl","a")
        pyautogui.press("backspace")

        # type DOC_ID folder
        pyautogui.write(str((f / DOC_ID).resolve()))
        pyautogui.press("enter")

        time.sleep(1)
        # This sequence empirically seems to work. Chrome (Versione 133.0.6943.53) Open file dialog (Windows 11 Enterprise 10.0.26100 build 26100)
        pyautogui.press("enter")
        pyautogui.press("enter")
        pyautogui.press("enter")
        time.sleep(1)

        pyautogui.write(files_string)

        pyautogui.press("enter")
        pyautogui.press("enter")

        RETRY = 0
        while True:
            try:
                clickImage("back_to_doc_list.png",CONF=0.9)
                break
            except pyautogui.ImageNotFoundException:
                RETRY += 1
                if RETRY > 3:
                    break

        with open("QUEUE_DONE.TXT","a") as fd:
            fd.write(DOC_ID + "\n")

        print("To stop press ctrl+c TWO TIMES (5 seconds)")
        time.sleep(5)
except KeyboardInterrupt :
    print("ctrl + c pressed. hope you did it when you could do it because rollback is not implemented")
    # TODO rollback last iteration

f_to_url = Path(MAP_JSON_PATH)
f_to_url.touch()

with open(f_to_url,"w") as fd:
    json.dump(MAP_FOLDER_TO_ESCR_DOC,fd)
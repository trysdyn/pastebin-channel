"""
The Pastebin Channel v1.2

Scrolls the contents of Pastebin's recent public pastes along a simple Pygame
window, allowing for kiosk style display of Pastebin's content.
"""

import urllib2
import pygame
import time
import webbrowser
from pygame.locals import *
from HTMLParser import HTMLParser

# Various editable options
print_help = True

win_width = 800
win_height = 600

fps = 30
scroll_rate = 1

font_face = ["DejaVu Sans Mono", 14]
font_color = (255, 255, 255)
bg_color = (0, 0, 0)
max_linewidth = 250

# Do not edit below this line
quit = False
paused = False
move_frame = False
raw_url = "http://www.pastebin.com/raw.php?i="
archive_url = "http://pastebin.com/archive"
text_lines = []
parser = None


class Line:
    """
    A single line to be displayed in the window, represented by a single pygame
    surface. Metadata stored so events that necessitate re-creation of the
    surface (resize, mostly) can be executed quickly.
    """
    destroy = False
    content = None
    line = None
    text = None
    color = None
    x = 5
    y = 5

    def __init__(self, content, color=font_color, link=None):
        # Truncate the line, since a surface of sufficient width can crash pygame
        if len(content) > max_linewidth:
            content = content[0:max_linewidth]

        self.content = text_font.render(content, 1, color, bg_color)
        self.color = color
        self.text = content
        self.link = link

        # Place the line at the bottom of the view, directly under the last
        if not len(text_lines):
            self.y = win_height
        else:
            self.y = text_lines[-1].y + font_face[1] + 2

    def update(self):
        """
        Move the line the appropriate number of pixels for a single refresh,
        then re-blit it.
        """
        self.y -= scroll_rate

        if self.y < -win_height:
            self.destroy = True
            return
        elif self.y <= win_height:
            screen.blit(self.content, (self.x, self.y))

    def check_click(self, pos):
        """
        Check if a given position is within this line and, if so, launch the
        user's default web browser to open the paste as is on pastebin.com
        """
        if pos[1] >= self.y and pos[1] < self.y + font_face[1]:
            if self.link is not None:
                webbrowser.open(self.link)


class ArchiveParser(HTMLParser):
    """
    Parases the Pastebin Archive at http://www.pastebin.com/archive and returns
    a dict where paste_id = (title, format).

    Since the Pastebin APi lacks functionality to do what we want, we have to
    page scum (I know, bad!).
    """
    results = {}       # PasteID => (Format, Title)
    this_result = ""   # Temporary storage for the Paste ID of a result
    this_title = ""    # Temporary storage for the Title of a result
    parsing_table = False
    parsing_title = False

    def handle_starttag(self, tag, attrs):
        # If parsing_table is true, we're in the list of Pastes
        if self.parsing_table:
            if tag == "a":
                # Find all hrefs and build a dict of pastes
                for attr in attrs:
                    if attr[0] == "href":
                        # hrefs starting with /archive indicate the end of paste data, and also the paste format
                        if attr[1].startswith("/archive"):
                            self.results[self.this_result] = (attr[1].split("/")[2], self.this_title)
                        # Otherwise the href is the paste ID, the data of this <a> is the title
                        else:
                            self.this_result = attr[1][1:]
                            self.parsing_title = True
        elif tag == "table" and ('class', 'maintable') in attrs:
            self.parsing_table = True

    def handle_endtag(self, tag):
        # If we find the end of the table of Pastes, we can stop parsing
        if self.parsing_table and tag == "table":
            self.parsing_table = False

    def handle_data(self, data):
        # Grab the Title of a Paste and then stop looking for Titles
        if self.parsing_title:
            self.this_title = data
            self.parsing_title = False


def get_paste(paste_id):
    """
    Grabs the raw data of the paste with ID paste_id and returns it.
    """
    paste_url = raw_url + paste_id
    req = urllib2.Request(paste_url)
    response = urllib2.urlopen(req)
    text = response.read()

    try:
        # Try to encode in unicode, using the content-type header
        encoding = response.headers['content-type'].split('charset=')[-1]
        text = unicode(text, encoding)
    except:
        # If it fails we're not horribly concerned...
        pass

    return text


def redraw_lines():
    """
    In the event of a text resize, we need to redraw all lines. This dumps line
    metadata to a temporary list, then redraws lines one by one as surfaces.
    """
    global text_lines

    text_cache = [(line.text, line.color) for line in text_lines if not line.destroy]
    text_lines = []
    for line in text_cache:
        text_lines.append(Line(line[0], color=line[1]))

    scroll_all(-win_height)


def scroll_all(distance):
    """
    Loops through the list of lines and moves them 'distance' pixels up.
    """
    for line in text_lines:
        line.y += distance

    global move_frame
    move_frame = True


def generate_output(paste_id):
    """
    Calls the functions to grab a paste from Pastebin, then parse and append it
    to the list of lines to be drawn.
    """
    try:
        for line in get_paste(paste_id).split('\n'):
            line = line.replace("\t", "     ")
            line = line.replace("\r", "")
            line = line.replace("\n", "")
            text_lines.append(Line(line, link="http://www.pastebin.com/%s" % paste_id))
    except:
        pass


# Setup stuff
pygame.init()
screen = pygame.display.set_mode((win_width, win_height), RESIZABLE)
pygame.display.set_caption("Pastebin Channel")
text_font = pygame.font.SysFont(*font_face)
clock = pygame.time.Clock()

# Print help at the top. Probably should be an external file
if print_help:
    text_lines.append(Line("PASTEBIN ROULETTE v1.2", color=(255, 255, 0)))
    text_lines.append(Line("Now with Unicode support (If your font supports it) and click-to-open support!", color=(255, 255, 0)))
    text_lines.append(Line("", color=(255, 255, 0)))
    text_lines.append(Line("UPARROW: Scroll Up", color=(255, 255, 0)))
    text_lines.append(Line("DOWNARROW: Scroll Down", color=(255, 255, 0)))
    text_lines.append(Line("KEYPAD +: Increase Font Size", color=(255, 255, 0)))
    text_lines.append(Line("KEYPAD -: Decrease Font Size", color=(255, 255, 0)))
    text_lines.append(Line("KEYPAD *: Increase Scroll Speed", color=(255, 255, 0)))
    text_lines.append(Line("KEYPAD /: Decrease Scroll Speed", color=(255, 255, 0)))
    text_lines.append(Line("SPACE: Pause / Resume Scrolling", color=(255, 255, 0)))
    text_lines.append(Line("CLICK: Open clicked Paste in default web browser", color=(255, 255, 0)))
    text_lines.append(Line("Escape: Quit", color=(255, 255, 0)))

while not quit:
    for event in pygame.event.get():
        # Window resized, resize the canvas to match
        if event.type == VIDEORESIZE:
            win_width = event.w
            win_height = event.h
            screen = pygame.display.set_mode((win_width, win_height), RESIZABLE)
        elif event.type == QUIT:
            quit = True
        elif event.type == KEYDOWN:
            # Space = Pause / Resume
            if event.key == K_SPACE:
                paused = False if paused else True
            # Escape = Quit
            elif event.key == K_ESCAPE:
                quit = True
            # Minus = Shrink text
            elif event.key == K_KP_MINUS:
                font_face[1] = font_face[1] - 2
                text_font = pygame.font.SysFont(*font_face)
                redraw_lines()
            # Plus = Enlargen text
            elif event.key == K_KP_PLUS:
                font_face[1] = font_face[1] + 2
                text_font = pygame.font.SysFont(*font_face)
                redraw_lines()
            # Asterisk = Increase scroll speed
            elif event.key == K_KP_MULTIPLY:
                scroll_rate += 1
            # Slash = Decrease scroll speed
            elif event.key == K_KP_DIVIDE:
                scroll_rate -= 1
            # Up = Scroll up
            elif event.key == K_UP:
                scroll_all(font_face[1] * 10)
            # Down = Scroll down
            elif event.key == K_DOWN:
                scroll_all(-font_face[1] * 10)
        elif event.type == MOUSEBUTTONDOWN:
            if event.button == 1:
                for line in text_lines:
                    line.check_click(event.pos)

    clock.tick(fps)

    # !pause or move_frame means we need to redraw stuff
    if not paused or move_frame:
        move_frame = False

        screen.fill(bg_color)

        # Move and redraw each line
        for line in text_lines:
            line.update()

        # If our buffer of lines is empty, grab another Paste
        if len(text_lines) == 0 or text_lines[-1].y < win_height:
            # If we're out of Pastes, grab the Archive page again
            if parser is None or len(parser.results.keys()) == 0:
                try:
                    req = urllib2.Request(archive_url)
                    response = urllib2.urlopen(req)
                    output = response.read()

                    try:
                        encoding = response.headers['content-type'].split('charset=')[-1]
                        output = unicode(output, encoding)
                    except:
                        pass

                    parser = ArchiveParser()
                    parser.feed(output)
                except Error as e:
                    time.sleep(10)

            # Grab a (Kind of random) key from the result dict
            next_result = parser.results.keys()[0]

            this_url = "http://www.pastebin.com/%s" % next_result

            text_lines.append(Line(""))
            text_lines.append(Line("###############################", color=(0, 255, 0), link=this_url))
            text_lines.append(Line("TITLE: %s" % parser.results[next_result][1], color=(0, 255, 0), link=this_url))
            text_lines.append(Line("FORMAT: %s" % parser.results[next_result][0], color=(0, 255, 0), link=this_url))
            text_lines.append(Line(this_url, color=(0, 255, 0), link=this_url))
            text_lines.append(Line("###############################", color=(0, 255, 0), link=this_url))
            text_lines.append(Line("", link=this_url))

            # Generate lines of text from the selected Paste then delete it from the result list
            generate_output(next_result)
            del(parser.results[next_result])

        # Remove any lines from memory that are scrolled past a certain threshold
        text_lines = [line for line in text_lines if not line.destroy]
        pygame.display.flip()


import curses
import os
import sys

if len(sys.argv) < 2: exit()

cursor = 0
mode = ""
nibble = 0
buf = ""
voffs = 0
LINES = COLS = 0
asc = False
with open(sys.argv[1], "rb") as f:
    data = bytearray(f.read())


def update_cursor(stdscr):
    global cursor
    cursor = min(len(data), max(0, cursor))
    if asc: stdscr.move(1 + cursor//16 - voffs, 61 + cursor%16)
    else: stdscr.move(1 + cursor//16 - voffs, 10 + 3*(cursor % 16))


def refresh_page(stdscr):
    global cursor, voffs
    cursor = min(len(data), max(0, cursor))
    if cursor//16 - voffs >= LINES - 2:
        voffs = cursor//16 - LINES + 3
    if cursor//16 - voffs < 0:
        voffs = cursor//16
    for r in range(1, LINES - 1):
        x = r - 1 + voffs
        n = min(16, len(data) - x*16)
        if n < 0: stdscr.addstr(r, 0, " "*(COLS-1))
        else: stdscr.addstr(r, 0, hex(16*x)[2:].rjust(8, '0') + "  " + " ".join(hex(data[i])[2:].rjust(2, "0") for i in range(16*x, 16*x+n)).ljust(48, " ") + ("  |"+"".join(chr(x) if x >= 32 else '.' for x in data[16*x:16*x+n])+"|").ljust(20, " "))
    update_cursor(stdscr)
    stdscr.refresh()


def main(stdscr):
    global mode, cursor, data, nibble, buf, LINES, COLS, asc
    stdscr.clear()
    LINES, COLS = stdscr.getmaxyx()
    stdscr.addstr(0, 0, "Command line hex editor")
    refresh_page(stdscr)
    while True:
        k = stdscr.getch()
        if k == curses.KEY_RESIZE:
            LINES, COLS = stdscr.getmaxyx()
            continue
        if buf:
            if k == ord("\n"):
                if "w" in buf:
                    with open(sys.argv[1], "wb") as f: f.write(data)
                if "q" in buf: break
                buf = ""
            elif k == 27:
                stdscr.addstr(LINES-1, 0, " "*(COLS-1))
                stdscr.refresh()
                update_cursor(stdscr)
                buf = ""
            else:
                buf += chr(k)
                stdscr.addstr(LINES-1, len(buf)-1, chr(k))
                stdscr.refresh()
            continue
        if k == 27: 
            mode = ""
            buf = ""
            stdscr.addstr(LINES-1, 0, "             ")
            update_cursor(stdscr)
            stdscr.refresh()
        if mode == "":
            if k == ord(":") and buf == "":
                buf = ":"
                stdscr.addstr(LINES-1, 0, ":")
                stdscr.refresh()
            elif k == ord("i"):
                mode = "i"
                stdscr.addstr(LINES-1, 0, "-- INSERT -- ")
                update_cursor(stdscr)
                stdscr.refresh()
                nibble = 0
                continue
            elif k == ord("R"):
                mode = "R"
                stdscr.addstr(LINES-1, 0, "-- REPLACE --")
                update_cursor(stdscr)
                stdscr.refresh()
                nibble = 0
                continue
            elif k == ord("\t"):
                asc = not asc
                update_cursor(stdscr)
        if k == curses.KEY_RIGHT:
            cursor += 1
            refresh_page(stdscr)
        elif k == curses.KEY_LEFT:
            cursor -= 1
            refresh_page(stdscr)
        elif k == curses.KEY_DOWN:
            cursor += 16
            refresh_page(stdscr)
        elif k == curses.KEY_UP:
            cursor -= 16
            refresh_page(stdscr)
        if k > 255 or k < 0: continue
        elif chr(k) in "0123456789abcdefABCDEF" and mode and mode in "iR" and not asc:
            if nibble == 0 and mode == "i":
                data.insert(cursor, 0)
            data[cursor] = (0xff & (data[cursor] << 4)) | int(chr(k), 16)
            if nibble == 1:
                cursor += 1
            refresh_page(stdscr)
            nibble = 1 - nibble
        elif k == 127:
            cursor -= 1
            del data[cursor]
            refresh_page(stdscr)
        elif mode and mode in "iR" and asc:
            if mode == "i": data.insert(cursor, k)
            elif cursor < len(data)-1: data[cursor] = k
            cursor += 1
            refresh_page(stdscr)

os.environ.setdefault('ESCDELAY', '25')
curses.wrapper(main)


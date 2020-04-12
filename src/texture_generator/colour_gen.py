from PIL import Image

OLD_PATH = "../../resources/objects/animated/flag_100_sprite.png"
NEW_PATH = "../../resources/objects/animated/flag_100_sprite_blue.png"

MATRIX_BLUE = [(0,0,1), (0,1,0), (1,0,0)]

MATRIX_GREEN = [(0,1,0), (1,0,0), (0,0,1)]

MATRIX_TEAL = [(0,0,0), (0.5,0.8,0.2), (0.5,0,1)]

MATRIX_YELLOW = [(1,0,0), (1,0,0), (0,0,0)]

MATRIX_PINK = [(1,0,0), (0,0,0), (1,0,0)]

IGNORE_1 = [(170, 190), (140, 160), (40, 70)]
IGNORE_2 = [(130, 150), (130, 140), (102, 112)]

def change_color(m, path: str, new_path: str):
    img: Image = Image.open(path)
    pixels = img.load() # create the pixel map
    ignore_list = []
    ignore_list.append(IGNORE_1)
    ignore_list.append(IGNORE_2)

    for i in range(img.size[0]): # for every pixel:
        for j in range(int(img.size[1])):
            r, g, b, a = pixels[i, j]
            change = True
            for ig in ignore_list:
                if ig[0][0] < r < ig[0][1] and \
                    ig[1][0] < g < ig[1][1] and \
                    ig[2][0] < b < ig[2][1]:
                    change = False
            if not change:
                continue
            r_new = min(m[0][0] * r + m[0][1] * g + m[0][2] * b, 255)
            g_new = min(m[1][0] * r + m[1][1] * g + m[1][2] * b, 255)
            b_new = min(m[2][0] * r + m[2][1] * g + m[2][2] * b, 255)

            pixels[i, j] = (int(r_new), int(g_new), int(b_new), a)

    img.save(new_path)

change_color(MATRIX_BLUE, OLD_PATH, "../../resources/objects/animated/flag_100_sprite_{}.png".format('blue'))
change_color(MATRIX_GREEN, OLD_PATH, "../../resources/objects/animated/flag_100_sprite_{}.png".format('green'))
change_color(MATRIX_TEAL, OLD_PATH, "../../resources/objects/animated/flag_100_sprite_{}.png".format('teal'))
change_color(MATRIX_YELLOW, OLD_PATH, "../../resources/objects/animated/flag_100_sprite_{}.png".format('yellow'))
change_color(MATRIX_PINK, OLD_PATH, "../../resources/objects/animated/flag_100_sprite_{}.png".format('pink'))


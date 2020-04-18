from PIL import Image, ImageOps
import glob, os


# im1 = Image.open('stone_var0.bmp')
# im2 = Image.open('dg_var0.png')
#
# mask = Image.open('mask_round.bmp')
#
# small_mask_2 = mask.crop((33, 0, 66+33, 64+0)).convert('L')
# small_mask_1 = mask.crop((99, 0, 66+99, 64+0)).convert('L')
#
#
# # inv masks:
# small_mask_1 = ImageOps.invert(small_mask_1)
#
# im_res_2 = Image.composite(im1, im2, small_mask_1)
# im_res_1 = Image.composite(im1, im2, small_mask_2)
#
# im_res_1.save('result_1.png', quality=95)
# im_res_2.save('result_2.png', quality=95)


# ROOT_STORE:
ROOT = "../../resources/generated/"
ROOT_FORESTS = "../../resources/objects/forests/"
TILE_WIDTH = 66
TILE_HIGHT = 64

MASK_ROOT = "./masks/"
MAKS_OFFSET = [(99, 0), (132, 26), (99, 52),
               (33, 52), (0, 26), (33, 0)]
MASK_CODE = ["1_4", "2_5", "3_6", "3_5", "4_6", "1_5", "2_6", "1_3", "2_4"]


def generate_merged_textures(path_tex_1: str, path_tex_2: str, res_str: str, inv: bool = False, var: int = 0):
    tex_1 = Image.open(path_tex_1)
    tex_2 = Image.open(path_tex_2)

    masks  = []

    masks.append(Image.open(MASK_ROOT + 'mask_1_4.bmp'))
    masks.append(Image.open(MASK_ROOT + 'mask_2_5.bmp'))
    masks.append(Image.open(MASK_ROOT + 'mask_3_6.bmp'))
    masks.append(Image.open(MASK_ROOT + 'mask_round.bmp'))

    current_mask = None
    for i in range(9):
        if i <= 2:
            current_mask = masks[i].convert('L')
            print(current_mask.size)
            if current_mask.size == (66, 66):
                current_mask = current_mask.crop((0, 2, TILE_WIDTH, TILE_HIGHT+2)).convert('L')
            # if not inv:
            #     current_mask = ImageOps.invert(current_mask)

        else:
            current_mask = masks[3]
            current_mask = current_mask.crop((MAKS_OFFSET[i-3][0], MAKS_OFFSET[i-3][1],
                                          MAKS_OFFSET[i-3][0] + TILE_WIDTH,
                                          MAKS_OFFSET[i-3][1] + TILE_HIGHT)).convert('L')
        if inv:
            current_mask = ImageOps.invert(current_mask)

        res = Image.composite(tex_1, tex_2, current_mask)
        #res.save(ROOT + res_str + "_" + MASK_CODE[i] + "_var_" + str(var) + '.png', quality=95)
        res.save('{}{}_{}_var_{}.png'.format(ROOT, res_str, MASK_CODE[i], str(var)), quality=95)


def generate_texture_info():
    cur_dir = os.curdir
    os.chdir(ROOT_FORESTS)
    print("<!-- generated textures -->")
    for file in glob.glob("*.png"):
        name = file.split('.')[0]
        s = '\t \t<{} code="{}" offsetX="0" offsetY="0" scale="1">{}{}</{}>'.format(name, name,
                                                                                    "../resources/objects/forests/", file, name)
        print(s)
    print("\t \t<!-- end of generated textures -->")

    os.chdir(cur_dir)

# generate_merged_textures("lg_var0.png", "dg_var0.png", "dg_lg")
# generate_merged_textures("dg_var0.png", "lg_var0.png", "lg_dg")
# generate_merged_textures("stone_var0.bmp", "lg_var0.png", "st_lg")
# generate_merged_textures("lg_var0.png", "stone_var0.bmp", "lg_st")
# generate_merged_textures("stone_var0.bmp", "dg_var0.png", "st_dg")
# generate_merged_textures("dg_var0.png", "stone_var0.bmp", "dg_st")

generate_texture_info()
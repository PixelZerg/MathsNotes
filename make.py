#!/usr/bin/env python3
import random
import subprocess
import os
from PIL import Image, ImageChops

FADE_DURATION = 3
CUT_AMOUNT = 1

credit_dict = {
    "animenz": "https://www.youtube.com/user/Animenzzz",
    "animenz-departures": "https://www.youtube.com/watch?v=5hft807EJ6o",
    "animenz-hikaru-nara": "https://www.youtube.com/watch?v=zsVAbS8xmaU",
    "animenz-kuchizuke-diamond": "https://www.youtube.com/watch?v=P6C3szts5C4",
    "animenz-my-dearest": "https://www.youtube.com/watch?v=Pi8xsZXibIc",
    "animenz-my-soul-your-beats": "https://www.youtube.com/watch?v=eJInGGAPZgI",
    "animenz-nagi-no-asukara-medley": "https://www.youtube.com/watch?v=1zKejX-up-k",
    "animenz-this-game": "https://www.youtube.com/watch?v=JRQbVNzmCK0",
}

def run(*args, **kwargs):
    subprocess.run(*args, **kwargs, shell=True)

def get_length(path):
    result = subprocess.run("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {}".format(
        path
    ), shell=True, stdout=subprocess.PIPE)
    return float(result.stdout.decode('utf-8').strip())


def gen_imgs(path, padding=50):
    img = Image.open(path)
    bg = Image.new(img.mode, img.size, (255, 255, 255))
    diff = ImageChops.difference(img, bg)
    bbox = diff.getbbox()
    if bbox:
        img = img.crop(bbox)

    padded_im = Image.new("RGB", (img.size[0] + padding, img.size[1] + padding), color=(255, 255, 255))
    padded_im.paste(img, (padding // 2, padding // 2))
    padded_im.save(path)

    padded_im.crop((0, 0, padded_im.size[0], padded_im.size[0] // 16 * 9)).save(
        os.path.splitext(path)[0] + ".thumb.jpg",
        optimize=True, quality=80
    )

def choose_song(length):
    songs = []
    for song in os.listdir("music"):
        if get_length(os.path.join("music", song)) >= length:
            songs.append(song)

    if len(songs) <= 0:
        return random.choice(os.listdir("music"))
    else:
        return random.choice(songs)


if __name__ == '__main__':
    generated_imgs = []

    for chapter in [x for x in os.listdir('.')
                    if os.path.isdir(x)
                       and not x == 'res'
                       and not x.startswith('.')]:
        for part in sorted(set([os.path.splitext(x)[0] for x in os.listdir(chapter)
                                if not x.endswith('.autosave.xopp') and os.path.isfile(os.path.join(chapter, x))])):
            path = os.path.join(chapter, part)

            # generate image
            if not os.path.isfile(path + ".png") and os.path.isfile(path + ".xopp"):
                run("xournalpp -i {} {}".format(path + ".png", path + ".xopp"))
                generated_imgs.append("{} {}".format(
                    chapter.replace('_',' '),
                    part
                ).title())

            # crop image + gen thumbnail
            if os.path.isfile(path + ".png") and not os.path.isfile(path + ".thumb.jpg"):
                gen_imgs(path + ".png")

            # gen video
            if os.path.isfile(path + ".ogv") and not os.path.isfile(path + ".mp4"):
                length = get_length(path+".ogv")

                run("ffmpeg -y -i {} -ss {} -t {} -an -filter:v crop=1840:855:40:145 -c:v libx264 {}".format(
                    path + ".ogv",
                    CUT_AMOUNT,
                    length - CUT_AMOUNT*2,
                    path + ".tmp.mp4"
                ))

                length = get_length(path+".tmp.mp4")
                chosen_song = choose_song(length)
                run("ffmpeg -y -i {0} -stream_loop -1 -i {1} "
                    "-af 'afade=in:st=0:d={3},afade=out:st={4}:d={3},volume=0.2' "
                    "-fflags +shortest -max_interleave_delta 50000 "
                    "-c:v copy -c:a aac -shortest {2}".format(
                    path + ".tmp.mp4",
                    os.path.join("music", chosen_song),
                    path + ".mp4",
                    FADE_DURATION,
                    length - FADE_DURATION - 0.2
                ))
                os.remove(path+".tmp.mp4")

                with open(path+".desc.txt", "w") as f:
                    f.write("{} {}\n".format(
                        chapter.replace('_',' '),
                        part
                    ).title())
                    f.write('\n')

                    f.write("∥ Resources:\n")
                    f.write(" 🞄 final image: https://pixelzerg.github.io/MathsVids/{}\n".format(
                        chapter+"/"+part+".png"
                    ))
                    f.write(" 🞄 GitHub repo: https://github.com/PixelZerg/MathsVids\n")
                    f.write('\n')

                    f.write("∥ Software used:\n")
                    f.write(" 🞄 xournal++: https://github.com/xournalpp/xournalpp/\n")
                    f.write(" 🞄 recordmydesktop: http://recordmydesktop.sourceforge.net/\n")
                    f.write(" 🞄 ffmpeg: https://ffmpeg.org/\n")
                    f.write('\n')

                    song = os.path.splitext(chosen_song)[0]
                    dash_pos = song.find("-")
                    f.write("∥ Music:\n")
                    f.write(" 🞄 {} - {}: ".format(song[:dash_pos], song[dash_pos+1:].replace('-', ' ')).title() +
                            "{}\n".format(credit_dict[song]))
                    f.write('\n')

    if len(generated_imgs) > 0:
        msg = ''
        if len(generated_imgs) == 1:
            msg += "added: {}".format(generated_imgs[0])
        else:
            msg += "added files\n"
            for generated_img in generated_imgs:
                msg += "{}\n".format(generated_img)

        run("git add .")
        run("git commit -m \"{}\"".format(msg))
        run("git push origin master")


"""Geometry and language QA for the Persian presentation.

PowerPoint does not clip: a shape that runs past the slide edge or sits on top
of the footer is silently lost in the delivered file.  With no renderer in this
environment, the only reliable check is arithmetic on the shape geometry, which
is what this script does.

Checks: slide count, every shape inside the slide box, no picture overlapping
another picture or a footer element, Persian text present, and chart labels left
in English (matplotlib cannot shape Arabic script, so this is by design).
"""
import os
import re
import sys

from pptx import Presentation

DECK = "Siahmakan_Analysis/03_Presentation/Siah_Makan_Engineering_Performance_Presentation.pptx"
EXPECTED_SLIDES = 10


def main():
    if not os.path.exists(DECK):
        print("MISSING: %s" % DECK)
        return 1
    prs = Presentation(DECK)
    SW, SH = prs.slide_width, prs.slide_height
    fails = []

    if len(prs.slides) != EXPECTED_SLIDES:
        fails.append("slide count %d, expected %d" % (len(prs.slides), EXPECTED_SLIDES))

    print("%-5s %6s %6s %6s %8s %s" % ("slide", "shapes", "pics", "tables", "faChars", "verdict"))
    print("-" * 62)
    for i, s in enumerate(prs.slides, 1):
        pics = [sh for sh in s.shapes if sh.shape_type == 13]
        tbls = [sh for sh in s.shapes if sh.has_table]
        foot = [sh for sh in s.shapes if sh.top and sh.top > SH - 550000]
        fa = sum(len(re.findall(r"[\u0600-\u06FF]", sh.text_frame.text))
                 for sh in s.shapes if sh.has_text_frame)
        notes = []
        for sh in s.shapes:
            if sh.left is None:
                continue
            if (sh.left < -1000 or sh.top < -1000 or
                    sh.left + sh.width > SW + 1000 or sh.top + sh.height > SH + 1000):
                notes.append("out of bounds: %s" % sh.name)
        for pic in pics:
            for f in foot:
                if (pic.left < f.left + f.width and f.left < pic.left + pic.width and
                        pic.top < f.top + f.height and f.top < pic.top + pic.height):
                    notes.append("picture on footer")
        for a in range(len(pics)):
            for b in range(a + 1, len(pics)):
                A, B = pics[a], pics[b]
                if (A.left < B.left + B.width and B.left < A.left + A.width and
                        A.top < B.top + B.height and B.top < A.top + A.height):
                    notes.append("picture overlap")
        if fa < 100:
            notes.append("almost no Persian text")
        print("%-5d %6d %6d %6d %8d %s" % (i, len(s.shapes), len(pics), len(tbls), fa,
                                           "PASS" if not notes else "FAIL"))
        for n in notes:
            print("        - %s" % n)
            fails.append("slide %d: %s" % (i, n))

    print("\n%d slide(s); %d problem(s)" % (len(prs.slides), len(fails)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

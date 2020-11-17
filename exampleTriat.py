#!/usr/bin/python
import math
from pylab import *
from matplotlib.patches import Ellipse


def localizacion(a,b,c):
    """se localiza el dispositivo por medio de las
   fuerzas de las senales captadas y de la ubicacion de
   las antenas
    """
    d = 3
    i = 2.5
    j = -4
    #se definen las coordenadas de la Antena A
    ax = 0
    ay = 0
    #se define la cobertura Antena A
    ar = a
    #se definen las coordenadas de la Antena B
    bx = d
    by = 0
    #se definen las coordenadas de la Antena C
    br = b
    cx = i
    cy = j
    #se define la cobertura de la Antena c
    cr = c
    #se localiza la ubicacion del receptor
    x = (ar**2 - br**2 + d**2)/float((2*d))
    y = ((ar**2-br**2+i**2+j**2)/(2*j))-((float(i/j))*x)
    print "Tu estas ubicado en -> (%s,%s)" %(x, y)
    #grafica
    a = subplot(111, aspect='equal')
    e = Ellipse((ax,ay), ar*2, ar*2, 0)
    e.set_clip_box(a.bbox)
    e.set_color('green')
    e.set_alpha(0.1)
    a.add_patch(e)
    a.annotate("Antena A",
               xy=(ax, ay), xycoords='data',
               xytext=(ax-3, ay+3), textcoords='data',
               arrowprops=dict(arrowstyle="->",
                               connectionstyle="arc3"),
               )
    a.plot(ax,ay, "g^", mew=2, ms=12)
    a.add_artist(e)
    e = Ellipse((bx,by), 2*br,2*br, 0)
    e.set_clip_box(a.bbox)
    e.set_color('red')
    e.set_alpha(0.1)
    a.add_patch(e)
    a.annotate("Antena B",
               xy=(bx, by), xycoords='data',
               xytext=(bx+3, by+3), textcoords='data',
               arrowprops=dict(arrowstyle="->",
                               connectionstyle="arc3"))
    a.plot(bx,by, "r^", mew=2, ms=12)
    a.add_artist(e)
    e = Ellipse((cx,cy), 2*cr, 2*cr, 0)
    e.set_clip_box(a.bbox)
    e.set_color('blue')
    e.set_alpha(0.1)
    a.add_patch(e)
    a.annotate("Antena C",
               xy=(cx, cy), xycoords='data',
               xytext=(bx+3.5, by-6), textcoords='data',
               arrowprops=dict(arrowstyle="->",
                               connectionstyle="arc3"))
    a.plot(cx,cy, "b^", mew=2, ms=12)
    a.add_artist(e)
    a.plot(x,y, 'k*', mew=3, ms=12)
    xlim(-10, 10)
    ylim(-10, 10)
    show()


def main():
    """funcion principal
    """
    try:
        ar = float(sys.argv[1])
        br = float(sys.argv[2])
        cr = float(sys.argv[3])
    except:
        print "No seleccionaste las fuerzas de senal"
        return

    print "El dispositivo capta una senal de: "
    print "Antena A %s" %ar
    print "Antena B %s" %br
    print "Antena C %s" %cr
    localizacion(ar,br,cr)

main()

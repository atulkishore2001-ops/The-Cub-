import cairo, sys
import doodle as D
W,H=2000,900
s=cairo.ImageSurface(cairo.FORMAT_ARGB32,W,H); c=cairo.Context(s)
c.set_source_rgb(*D.CREAM); c.paint()
D.draw_char(c,"boy",dict(x=180,y=820,R=60,la1=150,ra1=150,la2=-10,ra2=-10))
D.draw_char(c,"girl",dict(x=420,y=820,R=60,la1=140,ra1=140,la2=-15,ra2=-15))
D.draw_char(c,"boy",dict(x=680,y=820,R=60,la1=20,ra1=150,ra2=60,tilt=-8,eyes="open",mouth="o",brows="raised",lookx=1))
D.draw_char(c,"girl",dict(x=940,y=820,R=60,la1=15,ra1=15,mouth="frown",brows="worried",eyes="open",pony=20,lean=-6))
D.draw_char(c,"boy",dict(x=1200,y=820,R=60,la1=60,ra1=60,la2=70,ra2=70,mouth="wavy",brows="worried",eyes="wide"))
D.draw_char(c,"girl",dict(x=1460,y=820,R=60,la1=100,ra1=100,mouth="big",eyes="happy",pony=-25,lk=30,rk=30,ll=20,rl=20))
D.draw_char(c,"boy",dict(x=1740,y=820,R=60,la1=10,ra1=120,ra2=30,mouth="talk",mouth_open=0.8,flip=-1,turn=0.6))
s.write_to_png(sys.argv[1])

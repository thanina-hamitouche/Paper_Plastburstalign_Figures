from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle, Polygon, Ellipse
from matplotlib.lines import Line2D

# Wide 2:1 layout, deliberately WITHOUT a title/header.
OUT = Path('workflow_output')
OUT.mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(20, 10), dpi=130)
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
ax.set_xlim(0, 20)
ax.set_ylim(0, 10)
ax.set_aspect('equal')
ax.axis('off')

YELLOW='#FFE48D'; PALE='#FFF4CD'; ORANGE='#F26435'; DARK='#23252A'
GRAY='#ECEDEF'; GRAY_STROKE='#989B9E'; LIGHT='#F9FAFC'; MUTED='#626870'
PURPLE='#E6D7FF'; PURPLE_EDGE='#AE88EA'; GREEN='#76AF55'

def box(x,y,w,h,fill=YELLOW,edge=ORANGE,r=.22,lw=1.8,dashed=False,z=2):
    p=FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0.015,rounding_size={r}',
        fc=fill, ec=edge, lw=lw, linestyle='--' if dashed else '-',zorder=z)
    ax.add_patch(p); return p

def txt(x,y,s,size=11,bold=False,ha='center',va='center',color=DARK,linespace=1.18,z=6):
    ax.text(x,y,s,fontsize=size,weight='bold' if bold else 'normal',ha=ha,va=va,
            color=color,linespacing=linespace,zorder=z)

def arrow(x1,y1,x2,y2,color=ORANGE,dashed=False,lw=2.5,ms=16):
    p=FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=ms,
        lw=lw, color=color, linestyle='--' if dashed else '-',shrinkA=0,shrinkB=0,zorder=5)
    ax.add_patch(p)

def route(points,color=ORANGE,dashed=False,lw=2.5):
    for a,b in zip(points[:-2],points[1:-1]):
        ax.add_line(Line2D([a[0],b[0]],[a[1],b[1]],color=color,lw=lw,
                 linestyle='--' if dashed else '-',zorder=1))
    arrow(*points[-2],*points[-1],color=color,dashed=dashed,lw=lw)

def file_icon(x,y,s=.6,label='FASTA',edge=ORANGE):
    w=s*.76;h=s
    poly=Polygon([(x,y),(x+w,y),(x+w,y+h*.80),(x+w*.77,y+h),(x,y+h)],
        fc='white',ec=edge,lw=1.7,zorder=5)
    ax.add_patch(poly)
    ax.add_line(Line2D([x+w*.77,x+w*.77],[y+h,y+h*.80],color=edge,lw=1.2,zorder=6))
    ax.add_line(Line2D([x+w*.77,x+w],[y+h*.80,y+h*.80],color=edge,lw=1.2,zorder=6))
    for off in [.30,.43,.56]:
        ax.add_line(Line2D([x+w*.15,x+w*.82],[y+h*off]*2,color=edge,lw=1,zorder=6))
    if label:
        ax.add_patch(Rectangle((x-w*.10,y+h*.13),w*1.18,h*.22,fc=edge,ec='none',zorder=7))
        txt(x+w*.49,y+h*.24,label,size=7,bold=True,color='white',z=8)

def rows(x,y,w,n=3,step=.22):
    for i in range(n):
        yy=y-i*step
        ax.add_patch(Rectangle((x,yy),w,.11,fc='#CED1D4',ec='none',zorder=5))
        for pos in [.18,.39,.61,.79,.92]:
            if (i+int(pos*10))%4 != 0:
                xx=x+w*pos
                ax.add_line(Line2D([xx,xx],[yy-.015,yy+.13],color='#262626',lw=1.5,zorder=6))

def marker_diagram(x,y,kind):
    # minimal literal schematic, not decorative DNA art
    ax.add_line(Line2D([x,x+1.5],[y,y],lw=1.2,color=DARK,zorder=6))
    if kind=='CDS':
        for p,w in [(.15,.24),(.52,.35),(1.12,.20)]:
            ax.add_patch(Rectangle((x+p,y-.09),w,.18,fc='#F7D27A',ec=DARK,lw=1,zorder=6))
    elif kind=='INT':
        for p,w in [(.1,.24),(.99,.25)]:
            ax.add_patch(Rectangle((x+p,y-.09),w,.18,fc='#F7D27A',ec=DARK,lw=1,zorder=6))

def worker(x,y,name):
    box(x,y,1.17,.39,fill=PURPLE,edge=PURPLE_EDGE,r=.18,lw=1.1,z=4)
    txt(x+.585,y+.195,name,size=10,bold=True)
    arrow(x+1.22,y+.195,x+1.57,y+.195,ms=11,lw=1.8)
    box(x+1.62,y-.01,2.74,.41,fill='white',edge='#F0F0F0',r=.15,lw=.3,z=3)
    rows(x+1.78,y+.14,2.42,n=1)

# ---- Left: inputs ----
box(.20,6.11,3.0,2.38,fill=GRAY,edge=GRAY_STROKE)
file_icon(.47,7.61,.58,'GB',edge='#70767A')
txt(1.93,8.00,'Annotated plastid\ngenomes',size=13,bold=True)
txt(1.93,7.26,'(GenBank format)',size=10,color=MUTED)
# restrained circular plastome schematic
ax.add_patch(Circle((1.72,6.64),.37,fill=False,ec=GREEN,lw=5,zorder=5))
ax.add_patch(Ellipse((1.72,6.64),.42,.22,angle=25,fc='#B9DF9F',ec=GREEN,lw=1.4,zorder=5))

box(.20,2.80,3.0,2.97,fill=GRAY,edge=GRAY_STROKE,dashed=True)
file_icon(.45,5.02,.52,'YAML',edge='#787D81')
txt(1.92,5.32,'Configuration file',size=12.5,bold=True)
txt(1.92,4.96,'(optional)',size=10,color=MUTED)
for i,s in enumerate(['Region selection','Alignment tool','Length / taxon filters','Threads / CPU budget']):
    txt(.47,4.50-i*.40,'•  '+s,size=10,ha='left')

# ---- Extraction ----
box(3.70,2.80,3.22,5.69)
txt(5.31,8.04,'Extract & filter\nsequences',size=16,bold=True)
box(3.91,5.36,2.80,1.92,fill=PALE,edge='#FFF0B0',lw=.5,r=.13)
for y,label,kind in [(6.90,'CDS','CDS'),(6.39,'INT','INT'),(5.88,'IGS','IGS'),(5.50,'tRNA / rRNA',None)]:
    txt(4.08,y,label,size=10.8,bold=True,ha='left')
    if kind:
        marker_diagram(5.05,y-.03,kind)
box(3.91,3.04,2.80,2.11,fill=PALE,edge='#FFF0B0',lw=.5,r=.12)
for i,s in enumerate(['Splice CDS exons','Normalize region names','Check CDS completeness','Handle duplicates','Filter length / taxa']):
    yy=4.82-i*.36
    txt(4.10,yy,'✓',size=12,bold=True,ha='left')
    txt(4.41,yy,s,size=9.2,ha='left')

# ---- Homologous grouping ----
box(7.42,2.80,3.02,5.69)
file_icon(8.68,7.78,.52,'FASTA')
txt(8.93,7.20,'Homologous sequences\nin FASTA format',size=15,bold=True)
cols=[('gene1',7.72),('gene2',8.64),('gene3',9.55)]
for g,cx in cols:
    txt(cx,6.31,g,size=11.5,bold=True,ha='left')
    for j,line in enumerate(['>sp1','ATGA…','>sp2','ATCG…','>sp3','ATGT…']):
        txt(cx,5.92-j*.43,line,size=9.6,ha='left')
file_icon(8.70,3.10,.52,'FASTA')

# ---- Alignment: large panel ----
box(10.96,1.75,5.62,6.74)
txt(13.77,8.05,'Multiple sequence alignment',size=16.5,bold=True)
txt(13.77,7.67,'Parallel across homologous markers',size=11.2)
txt(13.77,7.35,'MAFFT  /  MUSCLE  /  Clustal Omega',size=10,color=MUTED)

box(11.16,5.83,5.20,1.24,fill=PALE,edge='#F8C58F',dashed=True,lw=1,r=.17)
box(11.32,6.14,1.11,.54,fill='#FFE3A8',edge='#F3BF71',r=.13,lw=.8)
txt(11.88,6.41,'CDS',size=12,bold=True)
box(12.76,6.07,1.60,.69,fill=GRAY,edge='#E0E1E4',r=.13,lw=.6)
txt(13.56,6.42,'Protein-guided\nalignment',size=10)
box(14.67,6.07,1.52,.69,fill=GRAY,edge='#E0E1E4',r=.13,lw=.6)
txt(15.43,6.42,'Back-translation\nto codons',size=9.5)
arrow(12.48,6.41,12.73,6.41,lw=1.7,ms=12)
arrow(14.39,6.41,14.64,6.41,lw=1.7,ms=12)

box(11.16,4.40,5.20,1.24,fill=PALE,edge='#F8C58F',dashed=True,lw=1,r=.17)
box(11.32,4.68,1.42,.64,fill='#FFE3A8',edge='#F3BF71',r=.13,lw=.8)
txt(12.03,5.00,'INT / IGS\nRNA',size=10.4,bold=True)
box(13.15,4.67,2.34,.66,fill=GRAY,edge='#E0E1E4',r=.13,lw=.6)
txt(14.32,5.0,'Nucleotide alignment',size=10.3)
arrow(12.78,5.00,13.11,5.00,lw=1.7,ms=12)

ax.add_line(Line2D([11.26,16.25],[4.17,4.17],lw=1,color='#D7AA78',zorder=5))
worker(11.37,3.51,'Worker 1')
worker(11.37,2.94,'Worker 2')
txt(11.91,2.66,'⋮',size=15,bold=True)
worker(11.37,2.20,'Worker N')
txt(13.77,1.93,'Concurrent alignment of multiple markers',size=10)

# ---- Output and optional branch ----
box(17.05,5.03,2.72,3.46,fill=GRAY,edge=GRAY_STROKE)
txt(18.41,8.00,'Per-marker\naligned FASTA',size=14.3,bold=True)
txt(18.41,7.34,'(output)',size=10,color=MUTED)
box(17.25,5.24,2.34,1.91,fill='white',edge='#E3E5E7',r=.13,lw=.7)
txt(17.46,6.95,'>rbcL',size=10.5,bold=True,ha='left')
rows(17.46,6.70,1.92,n=3,step=.17)
txt(17.46,6.13,'>matK',size=10.5,bold=True,ha='left')
rows(17.46,5.93,1.92,n=3,step=.17)

box(17.05,2.60,2.72,1.87,fill=GRAY,edge=GRAY_STROKE,dashed=True)
file_icon(17.27,3.66,.44,'',edge='#767C80')
txt(18.52,4.04,'Concatenated\nalignment',size=12.5,bold=True)
txt(18.52,3.45,'(optional)',size=10,color=MUTED)
txt(17.28,2.99,'• Combine aligned markers\n• FASTA / NEXUS',size=9.2,ha='left',linespace=1.6)

# Arrows behind boxes; endpoints at box boundaries
route([(3.20,7.04),(3.45,7.04),(3.45,5.90),(3.68,5.90)],color=GRAY_STROKE,lw=2)
route([(3.20,4.29),(3.49,4.29),(3.49,5.55),(3.68,5.55)],color=GRAY_STROKE,dashed=True,lw=1.8)
arrow(6.94,5.63,7.40,5.63)
arrow(10.46,5.63,10.94,5.63)
arrow(16.60,5.63,17.03,5.63)
arrow(18.41,5.00,18.41,4.49,color=GRAY_STROKE,dashed=True,lw=2)

# ---- Legend ----
box(.40,.82,.57,.35,fill=YELLOW,edge=ORANGE,r=.10,lw=1.4)
arrow(1.00,1.00,1.50,1.00,ms=12,lw=1.7)
txt(1.68,1.00,'Required processing',size=11,bold=True,ha='left')
box(4.48,.82,.57,.35,fill=GRAY,edge=GRAY_STROKE,dashed=True,r=.10,lw=1.4)
arrow(5.08,1.00,5.58,1.00,color=GRAY_STROKE,dashed=True,ms=12,lw=1.7)
txt(5.76,1.00,'Optional',size=11,bold=True,ha='left')
box(7.38,.82,.57,.35,fill=GRAY,edge=GRAY_STROKE,r=.10,lw=1.4)
txt(8.18,1.00,'Input / output',size=11,bold=True,ha='left')

fig.subplots_adjust(left=.015,right=.985,bottom=.03,top=.985)
for ext in ['png','svg','pdf']:
    fig.savefig(OUT/f'plastburstalign_workflow.{ext}',dpi=220,bbox_inches='tight',facecolor='white')
plt.close(fig)
print('Wrote files to',OUT.resolve())

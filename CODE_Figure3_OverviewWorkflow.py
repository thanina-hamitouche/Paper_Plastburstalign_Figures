from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Polygon
from matplotlib.lines import Line2D

# Wide 2:1 layout, deliberately WITHOUT a title/header.
OUT = Path('./VIZ_Figure3_OverviewWorkflow/')
OUT.mkdir(parents=True, exist_ok=True)
fig, ax = plt.subplots(figsize=(20, 10), dpi=130)
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
ax.set_xlim(0, 20)
ax.set_ylim(0, 8.7)
ax.set_aspect('auto')
ax.axis('off')

BLACK='#000000'; YELLOW='#D9D9D9'; PALE='#E6E6E6'; ORANGE=BLACK; DARK=BLACK
GRAY='#FFFFFF'; GRAY_STROKE=BLACK; LIGHT='#F9F9F9'; MUTED='#404040'
PURPLE='#D0D0D0'; PURPLE_EDGE=BLACK
FIELD_TITLE_SIZE=17.5
FIELD_TEXT_SIZE=14.0

def box(x,y,w,h,fill=YELLOW,edge=ORANGE,r=.22,lw=1.8,dashed=False,z=2):
    p=FancyBboxPatch((x,y),w,h,boxstyle=f'round,pad=0.015,rounding_size={r}',
        fc=fill, ec=BLACK, lw=lw, linestyle='--' if dashed else '-',zorder=z)
    ax.add_patch(p); return p

def txt(x,y,s,size=11,bold=False,ha='center',va='center',color=DARK,linespace=1.18,z=6):
    ax.text(x,y,s,fontsize=size,weight='bold' if bold else 'normal',ha=ha,va=va,
            color=color,linespacing=linespace,zorder=z)

def field_title(x,y,s):
    ax.text(x,y,s,fontsize=FIELD_TITLE_SIZE,weight='bold',ha='center',va='center',
            color=DARK,linespacing=1.1,zorder=6)

def field_text(x,y,s,ha='center',color=DARK,linespace=.95):
    ax.text(x,y,s,fontsize=FIELD_TEXT_SIZE,weight='normal',ha=ha,va='center',
            color=color,linespacing=linespace,zorder=6)

def arrow(x1,y1,x2,y2,color=ORANGE,dashed=False,lw=3.2,ms=18):
    ms=max(ms,18)
    p=FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=ms,
        lw=lw, color=BLACK, linestyle='--' if dashed else '-',shrinkA=0,shrinkB=0,zorder=5)
    ax.add_patch(p)

def file_icon(x,y,s=.52,label='FASTA',edge=ORANGE,label_size=7,halo=0):
    edge=BLACK
    w=s*.76;h=s
    poly=Polygon([(x,y),(x+w,y),(x+w,y+h*.80),(x+w*.77,y+h),(x,y+h)],
        fc='white',ec=edge,lw=1.7,zorder=5,
        path_effects=[path_effects.Stroke(linewidth=1.7+halo,foreground='white'),
                      path_effects.Normal()] if halo else None)
    ax.add_patch(poly)
    ax.add_line(Line2D([x+w*.77,x+w*.77],[y+h,y+h*.80],color=edge,lw=1.2,zorder=6))
    ax.add_line(Line2D([x+w*.77,x+w],[y+h*.80,y+h*.80],color=edge,lw=1.2,zorder=6))
    for off in [.30,.43,.56]:
        ax.add_line(Line2D([x+w*.15,x+w*.82],[y+h*off]*2,color=edge,lw=1,zorder=6))
    if label:
        ax.add_patch(Rectangle((x+w*.05,y+h*.13),w*.90,h*.22,fc=edge,ec='none',zorder=7))
        txt(x+w*.50,y+h*.24,label,size=label_size,bold=True,color='white',z=8)

def file_icon_group(cx,y,s=.52,label='FASTA',count=3):
    w=s*.76
    step=w*.95
    vertical_step=.06
    total=w+step*(count-1)
    x=cx-total/2
    y-=vertical_step*(count-1)/2
    for i in range(count):
        file_icon(x+i*step,y+i*vertical_step,s,label,edge=BLACK,label_size=6.2,halo=3)

def rows(x,y,w,n=3,step=.22):
    for i in range(n):
        yy=y-i*step
        ax.add_patch(Rectangle((x,yy),w,.11,fc='#D0D0D0',ec='none',zorder=5))
        for pos in [.18,.39,.61,.79,.92]:
            if (i+int(pos*10))%4 != 0:
                xx=x+w*pos
                ax.add_line(Line2D([xx,xx],[yy-.015,yy+.13],color='#262626',lw=1.5,zorder=6))

def marker_diagram(x,y,kind):
    # minimal literal schematic, not decorative DNA art
    ax.add_line(Line2D([x,x+1.5],[y,y],lw=1.2,color=DARK,zorder=6))
    if kind=='CDS':
        for p,w in [(.15,.24),(.52,.35),(1.12,.20)]:
            ax.add_patch(Rectangle((x+p,y-.09),w,.18,fc='#D9D9D9',ec=BLACK,lw=1,zorder=6))
    elif kind=='INT':
        for p,w in [(.1,.24),(.99,.25)]:
            ax.add_patch(Rectangle((x+p,y-.09),w,.18,fc='#D9D9D9',ec=BLACK,lw=1,zorder=6))

def worker(x,y,name):
    box(x,y,.93,.39,fill=PURPLE,edge=PURPLE_EDGE,r=.18,lw=1.1,z=4)
    field_text(x+.465,y+.195,name)
    arrow(x+.93,y+.195,x+1.28,y+.195,lw=2.5)
    box(x+1.28,y-.01,2.77,.41,fill='white',edge='#F0F0F0',r=.15,lw=.3,z=3)
    rows(x+1.42,y+.14,2.48,n=1)

# ---- Input fields ----
box(.28,5.02,2.74,3.43,fill=GRAY,edge=GRAY_STROKE)
field_title(1.65,7.98,'Plastid genome\nrecords')
file_icon_group(1.65,7.05,.52,'GB')
field_text(1.65,6.72,'Format: GenBank flatfile',color=MUTED)

box(.28,1.45,2.74,3.30,fill=GRAY,edge=GRAY_STROKE,dashed=True)
field_title(1.65,4.43,'Configuration file')
file_icon(1.45,3.60,.52,'',edge=BLACK)
field_text(1.65,3.22,'Format: YAML',color=MUTED)
for y,s in zip([2.82,2.47,2.12,1.77],[
    'Region selection','Alignment tool','Length / taxon filters','Threads / CPU budget'
]):
    field_text(.49,y,'•  '+s,ha='left')

# ---- Extraction ----
box(3.45,1.45,3.20,7.00,fill=YELLOW,edge=ORANGE)
field_title(5.05,7.98,'Extraction & Filtering')
box(3.66,5.12,2.88,2.25,fill=PALE,edge=BLACK,lw=.8,r=.13)
for y,label,kind in [(6.98,'CDS','CDS'),(6.43,'INT','INT'),(5.88,'IGS','IGS'),(5.35,'tRNA / rRNA',None)]:
    field_text(3.82,y,label,ha='left')
    if kind:
        marker_diagram(4.92,y-.03,kind)
box(3.66,1.68,2.88,3.18,fill=PALE,edge=BLACK,lw=.8,r=.12)
for i,s in enumerate(['Splice CDS exons','Normalize regions','Check CDS completeness','Handle duplicates','Filter length / taxa']):
    yy=4.35-i*.42
    field_text(3.86,yy,'•',ha='left')
    field_text(4.05,yy,s,ha='left')

# ---- Homologous sequences ----
box(6.95,1.45,3.05,7.00,fill=YELLOW,edge=ORANGE)
field_title(8.475,7.98,'Grouping sequences\n by name')
file_icon_group(8.475,7.05,.52,'FASTA')
field_text(8.475,6.72,'Format: FASTA',color=MUTED)
cols=[('gene1',7.20),('gene2',8.10),('gene3',9.00)]
for g,cx in cols:
    field_text(cx,6.28,g,ha='left')
    for j,line in enumerate(['>sp1','ATGA…','>sp2','ATCG…','>sp3','ATGT…']):
        field_text(cx,5.85-j*.42,line,ha='left')

# ---- Multiple sequence alignment ----
box(10.30,.05,5.20,8.40,fill=PALE,edge=ORANGE)
field_title(12.90,7.98,'Multiple sequence alignment')
field_text(12.90,7.48,'Parallel across homologous markers')
field_text(12.90,7.07,'MAFFT / MUSCLE / Clustal Omega',color=MUTED)

box(10.55,5.72,4.70,1.15,fill=PALE,edge=BLACK,dashed=True,lw=1,r=.17)
box(10.75,5.97,.90,.54,fill='#D9D9D9',edge=BLACK,r=.13,lw=.8)
field_text(11.20,6.24,'CDS')
box(11.85,5.92,1.45,.64,fill=GRAY,edge=BLACK,r=.13,lw=.6)
field_text(12.575,6.24,'Protein-guided\nalignment')
box(13.50,5.92,1.55,.64,fill=GRAY,edge=BLACK,r=.13,lw=.6)
field_text(14.275,6.24,'Back-translation\nto codons')
arrow(11.65,6.24,11.85,6.24,lw=2.4)
arrow(13.30,6.24,13.50,6.24,lw=2.4)

box(10.55,4.34,4.70,1.16,fill=PALE,edge=BLACK,dashed=True,lw=1,r=.17)
box(10.75,4.60,1.50,.64,fill='#D9D9D9',edge=BLACK,r=.13,lw=.8)
field_text(11.50,4.92,'INT / IGS\nRNA')
box(12.65,4.60,2.40,.64,fill=GRAY,edge=BLACK,r=.13,lw=.6)
field_text(13.85,4.92,'Nucleotide alignment')
arrow(12.25,4.92,12.65,4.92,lw=2.4)

ax.add_line(Line2D([10.65,15.15],[4.15,4.15],lw=1,color=BLACK,zorder=5))
worker(10.86,3.48,'Worker 1')
worker(10.86,2.48,'Worker 2')
field_text(11.28,1.82,'⋮')
worker(10.86,.82,'Worker N')
field_text(12.90,.30,'Concurrent alignment of markers')

# ---- Output fields ----
box(15.80,4.65,4.05,3.80,fill=GRAY,edge=GRAY_STROKE)
field_title(17.825,7.98,'Marker-wise alignments')
file_icon_group(17.825,7.16,.52,'FASTA')
field_text(17.825,6.83,'Format: FASTA',color=MUTED)
box(16.05,4.88,3.55,1.76,fill='white',edge=BLACK,r=.13,lw=.8)
field_text(16.30,6.44,'>rbcL',ha='left')
rows(16.30,6.19,3.05,n=3,step=.15)
field_text(16.30,5.53,'>matK',ha='left')
rows(16.30,5.28,3.05,n=3,step=.15)

box(15.80,.05,4.05,4.35,fill=GRAY,edge=GRAY_STROKE,dashed=True)
field_title(17.825,4.08,'Concatenated alignment')
file_icon(17.628,3.25,.52,'',edge=BLACK)
field_text(17.825,2.90,'Format: FASTA / NEXUS',color=MUTED)
field_text(16.30,2.15,'• Combine aligned markers',ha='left')

# Workflow arrows
arrow(3.02,6.20,3.45,6.20)
arrow(3.02,3.20,3.45,3.20,color=GRAY_STROKE,dashed=True)
arrow(6.65,5.60,6.95,5.60)
arrow(10.00,5.60,10.30,5.60)
arrow(15.50,5.60,15.80,5.60)
arrow(17.825,4.65,17.825,4.40,color=GRAY_STROKE,dashed=True)

# ---- Legend ----
for y,label,fill,dashed in [
    (1.10,'Required',YELLOW,False),
    (.70,'Optional',GRAY,True),
    (.30,'Input / Output',GRAY,False),
]:
    box(.38,y-.175,.50,.35,fill=fill,edge=BLACK,dashed=dashed,r=.10,lw=1.4)
    if label != 'Input / Output':
        arrow(.88,y,1.30,y,color=BLACK,dashed=dashed,ms=14,lw=2.5)
    txt(1.42,y,label,size=FIELD_TEXT_SIZE,bold=True,ha='left')

fig.subplots_adjust(left=.015,right=.985,bottom=.03,top=.985)
for ext in ['png','svg','pdf']:
    fig.savefig(OUT/f'plastburstalign_workflow.{ext}',dpi=220,facecolor='white')
plt.close(fig)
print('Wrote files to',OUT.resolve())

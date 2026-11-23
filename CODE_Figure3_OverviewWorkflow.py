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
ax.set_xlim(0, 20.4)
ax.set_ylim(0, 9.0)
ax.set_aspect('auto')
ax.axis('off')

BLACK='#000000'; YELLOW='#E6E6E6'; PALE=YELLOW; ORANGE=BLACK; DARK=BLACK
GRAY='#FFFFFF'; GRAY_STROKE=BLACK; LIGHT=GRAY; MUTED=BLACK
SEQUENCE_GRAY='#A0A0A0'; PURPLE=SEQUENCE_GRAY; PURPLE_EDGE=BLACK
FONT_INCREASE=.5
FIELD_TITLE_SIZE=17.5+FONT_INCREASE
FIELD_TEXT_SIZE=14.0+FONT_INCREASE

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
        ax.add_patch(Rectangle((x,y+h*.13),w,h*.22,fc=edge,ec='none',zorder=7))
        txt(x+w*.50,y+h*.24,label,size=label_size+FONT_INCREASE,bold=True,color='white',z=8)

def file_icon_group(cx,y,s=.52,label='FASTA',count=3):
    w=s*.76
    step=w*.95
    vertical_step=.06
    total=w+step*(count-1)
    x=cx-total/2
    y-=vertical_step*(count-1)/2
    for i in range(count):
        file_icon(x+i*step,y+i*vertical_step,s,label,edge=BLACK,label_size=6.2,halo=4)

ALIGNMENT_GAP_WIDTH=.05
ALIGNMENT_ROW_STEP=.23

def alignment_rows(x,y,w,gaps,label_x=None):
    for i,positions in enumerate(gaps):
        yy=y-i*ALIGNMENT_ROW_STEP
        if label_x is not None:
            field_text(label_x,yy+.055,f'T{i+1}',ha='left')
        start=0
        for pos,count in positions:
            ax.add_patch(Rectangle((x+start*w,yy),(pos-start)*w,.11,
                                   fc=SEQUENCE_GRAY,ec='none',zorder=5))
            for j in range(count):
                ax.add_line(Line2D([x+(pos+j*ALIGNMENT_GAP_WIDTH+.01)*w,
                                    x+(pos+j*ALIGNMENT_GAP_WIDTH+.04)*w],
                                   [yy+.055,yy+.055],color=BLACK,lw=1.2,zorder=6))
            start=pos+count*ALIGNMENT_GAP_WIDTH
        ax.add_patch(Rectangle((x+start*w,yy),(1-start)*w,.11,
                               fc=SEQUENCE_GRAY,ec='none',zorder=5))

def marker_diagram(x,y,kind):
    ax.add_line(Line2D([x,x+1.22],[y,y],lw=1,color=BLACK,linestyle=':',zorder=5))
    for p,w,active in [(.02,.25,kind=='CDS'),(.48,.25,kind=='CDS'),
                       (1.00,.20,kind=='RNA')]:
        h=.18
        head=min(.09,w*.4)
        vertices=[(x+p,y-h/2),(x+p+w-head,y-h/2),(x+p+w,y),
                  (x+p+w-head,y+h/2),(x+p,y+h/2)]
        ax.add_patch(Polygon(vertices,closed=True,fc=BLACK if active else 'white',
                             ec=BLACK,lw=1,zorder=6))
    ax.add_patch(Rectangle((x+.27,y-.045),.21,.09,
        fc=BLACK if kind=='INT' else 'white',ec=BLACK,lw=1,zorder=6))
    if kind=='IGS':
        for i in range(4):
            ax.add_patch(Rectangle((x+.73+i*.0675,y-.09),.0675,.18,
                fc=BLACK if i%2==0 else 'white',ec='none',zorder=6))
        ax.add_patch(Rectangle((x+.73,y-.09),.27,.18,fill=False,ec=BLACK,lw=1,zorder=7))

def worker(x,y,name,gene,gaps,cores=1):
    box(x,y,1.12,.96,fill=PURPLE,edge=PURPLE_EDGE,r=.18,lw=1.1,z=4)
    field_text(x+.56,y+.79,name)
    field_text(x+.56,y+.52,f'{cores} CPU' if cores==1 else f'{cores} CPUs')
    for i in range(cores):
        cpu_icon(x+.56+(i-(cores-1)/2)*.14,y+.09+(cores-1-i)*.03,s=.20,z=6+i*2)
    arrow(x+1.12,y+.48,x+1.40,y+.48,lw=2.5)
    box(x+1.40,y,2.65,.96,fill='white',edge=BLACK,r=.15,lw=.3,z=3)
    field_text(x+1.50,y+.84,gene,ha='left')
    alignment_rows(x+1.99,y+.51,1.91,gaps,label_x=x+1.50)

def cpu_icon(cx,y,s=.24,z=6):
    x=cx-s/2
    for pos in (.25,.50,.75):
        ax.add_line(Line2D([x+s*pos,x+s*pos],[y-.04,y+s+.04],
                           color=BLACK,lw=1.1,zorder=z))
        ax.add_line(Line2D([x-.04,x+s+.04],[y+s*pos,y+s*pos],
                           color=BLACK,lw=1.1,zorder=z))
    ax.add_patch(Rectangle((x,y),s,s,fc='white',ec=BLACK,lw=1.2,zorder=z+0.1,
        path_effects=[path_effects.Stroke(linewidth=4,foreground='white'),
                      path_effects.Normal()]))
    ax.add_patch(Rectangle((x+s*.28,y+s*.28),s*.44,s*.44,
                           fc=SEQUENCE_GRAY,ec=BLACK,lw=.8,zorder=z+0.2))

# ---- Input fields ----
box(.28,5.02,2.74,3.63,fill=GRAY,edge=GRAY_STROKE)
field_title(1.65,7.95,'Plastid genome\nrecords')
file_icon_group(1.65,7.05,.52,'GB')
field_text(1.65,6.72,'Format: GenBank flatfile',color=MUTED)
ax.text(.46,6.43,'LOCUS     PLASTOME\nFEATURES\n     gene   1..90\n'
        '       /gene="rbcL"\nORIGIN\n        1 atgcaatgc\n//',
        fontsize=FIELD_TEXT_SIZE,fontfamily='monospace',ha='left',va='top',
        color=DARK,linespacing=.95,zorder=6)

box(.28,1.45,2.74,3.25,fill=GRAY,edge=GRAY_STROKE,dashed=True)
field_title(1.65,4.23,'Configuration file')
file_icon(1.45,3.53,.52,'',edge=BLACK)
field_text(1.65,3.22,'Format: YAML',color=MUTED)
for y,s in zip([2.82,2.47,2.12,1.77],[
    'Extraction mode','Alignment software','Length / taxon filters','Threads / CPU budget'
]):
    field_text(.39,y,'•  '+s,ha='left')

# ---- Extraction ----
box(3.45,.15,3.20,8.50,fill=YELLOW,edge=ORANGE)
field_title(5.05,7.98,'Marker extraction &\nquality control')
box(3.66,5.73,2.88,1.68,fill=PALE,edge=BLACK,lw=.8,r=.13)
for y,label,kind in [(7.14,'CDS','CDS'),(6.76,'INT','INT'),(6.38,'IGS','IGS'),(6.00,'tRNA / rRNA','RNA')]:
    field_text(3.82,y,label,ha='left')
    marker_diagram(5.17,y,kind)
box(3.66,2.86,2.88,2.65,fill=PALE,edge=BLACK,lw=.8,r=.12)
for i,s in enumerate(['• Extraction based on\n  different modes', '• Gene name\n  standardization', '• Marker deduplication', '• Exon concatenation', '• Coding sequence\n  validation']):
    yy=5.23-i*.48
    field_text(3.86,yy,s,ha='left')

ax.text(5.05,2.43,'Concurrent marker\nextraction',fontsize=FIELD_TITLE_SIZE,
        weight='bold',style='italic',ha='center',va='center',color=DARK,
        linespacing=1.1,zorder=6)
ax.add_line(Line2D([4.05,6.05],[1.99,1.99],color=BLACK,lw=2.5,zorder=5))
ax.add_line(Line2D([5.05,5.05],[2.10,1.99],color=BLACK,lw=2.5,zorder=5))
for i,x in enumerate((3.61,4.61,5.61),start=1):
    box(x,.50,.88,.96,fill=PURPLE,edge=PURPLE_EDGE,r=.18,lw=1.1,z=4)
    txt(x+.44,1.29,f'Worker {i}',size=FIELD_TEXT_SIZE-1.5)
    txt(x+.44,1.02,'1 CPU',size=FIELD_TEXT_SIZE-1.5)
    cpu_icon(x+.44,.59,s=.20)
    arrow(x+.44,1.99,x+.44,1.46,lw=2.5)

# ---- Homologous sequences ----
marker_gaps={
    '>gene1': [[(.22,1)],[(.63,2)],[]],
    '>gene2': [[(.63,3)],[],[(.22,2)]],
    '>gene3': [[],[(.18,1),(.34,1),(.50,2),(.68,3)],[(.12,2),(.28,2),(.44,3),(.62,2),(.78,3)]],
}
box(7.08,.15,3.05,8.50,fill=YELLOW,edge=ORANGE)
field_title(8.605,7.95,'Grouping & filtering\nsequences')
file_icon_group(8.605,7.05,.52,'FASTA')
field_text(8.605,6.72,'Format: FASTA',color=MUTED)
box(7.23,1.70,2.75,4.82,fill='white',edge=BLACK,r=.13,lw=.8)
for i,(gene,gaps) in enumerate(marker_gaps.items()):
    y=6.28-i*1.55
    field_text(7.33,y,gene,ha='left')
    for j,positions in enumerate(gaps):
        length=1.525*(1-sum(count*ALIGNMENT_GAP_WIDTH for _,count in positions))
        yy=y-.29-j*ALIGNMENT_ROW_STEP
        field_text(7.33,yy+.055,f'T{j+1}',ha='left')
        ax.add_patch(Rectangle((7.8425,yy),length,.11,
                               fc=SEQUENCE_GRAY,ec='none',zorder=5))
    field_text(8.605,y-1.07,'Anticipated alignm.\ncomplexity: '+('high' if i==2 else 'low'))
box(7.23,.50,2.75,.96,fill=PALE,edge=BLACK,r=.12,lw=.8)
field_text(7.43,1.14,'• Marker filtering',ha='left')
field_text(7.43,.80,'• Exclusion by marker\nname',ha='left')

# ---- Multiple sequence alignment ----
box(10.56,.15,5.20,8.50,fill=PALE,edge=ORANGE)
field_title(13.24,8.13,'Multiple sequence alignment')
field_text(13.16,7.55,'Alignment software:\nMAFFT / MUSCLE / Clustal Omega / others',color=MUTED)

box(10.81,5.97,4.70,1.15,fill=PALE,edge=BLACK,dashed=True,lw=1,r=.17)
box(10.91,6.22,.70,.54,fill=PALE,edge=BLACK,r=.13,lw=.8)
field_text(11.26,6.49,'CDS')
box(11.74,6.17,1.68,.64,fill=GRAY,edge=BLACK,r=.13,lw=.6)
field_text(12.58,6.49,'Codon-guided\nalignment')
box(13.55,6.17,1.86,.64,fill=GRAY,edge=BLACK,r=.13,lw=.6)
field_text(14.48,6.49,'Back-transl.\nto nucleotides')
arrow(11.61,6.49,11.74,6.49,lw=2.4)
arrow(13.42,6.49,13.55,6.49,lw=2.4)

box(10.81,4.59,4.70,1.16,fill=PALE,edge=BLACK,dashed=True,lw=1,r=.17)
box(11.01,4.85,1.50,.64,fill=PALE,edge=BLACK,r=.13,lw=.8)
field_text(11.76,5.17,'INT / IGS\nRNA')
box(12.91,4.85,2.40,.64,fill=GRAY,edge=BLACK,r=.13,lw=.6)
field_text(14.11,5.17,'Nucleotide-guided\nalignment')
arrow(12.51,5.17,12.91,5.17,lw=2.4)


ax.text(13.145,4.14,'Alignment multithreading',fontsize=FIELD_TITLE_SIZE,
        weight='bold',style='italic',ha='center',va='center',color=DARK,zorder=6)
worker(11.12,2.88,'Worker 1','>gene1',marker_gaps['>gene1'])
worker(11.12,1.76,'Worker 2','>gene2',marker_gaps['>gene2'])
worker(11.12,.56,'Worker 3','>gene3',marker_gaps['>gene3'],cores=3)

# ---- Output fields ----
box(16.19,4.65,4.05,4.00,fill=GRAY,edge=GRAY_STROKE)
field_title(18.215,8.10,'Marker-wise alignments')
file_icon_group(18.215,7.31,.52,'FASTA')
field_text(18.215,6.98,'Format: FASTA',color=MUTED)
box(17.015,4.84,2.40,1.95,fill='white',edge=BLACK,r=.13,lw=.8)
field_text(17.17,6.59,'>gene1',ha='left')
alignment_rows(17.69,6.33,1.525,marker_gaps['>gene1'],label_x=17.17)
field_text(17.17,5.67,'>gene2',ha='left')
alignment_rows(17.69,5.38,1.525,marker_gaps['>gene2'],label_x=17.17)

box(16.19,.15,4.05,4.17,fill=GRAY,edge=GRAY_STROKE,dashed=True)
field_title(18.215,3.81,'Concatenated alignment')
file_icon(18.018,3.09,.52,'FASTA',edge=BLACK)
field_text(18.215,2.90,'Format: FASTA / NEXUS',color=MUTED)
box(16.42,1.38,3.59,1.28,fill='white',edge=BLACK,r=.13,lw=.8)
field_text(16.64,2.48,'>concatenated',ha='left')
alignment_rows(17.10,2.12,1.35,marker_gaps['>gene1'],label_x=16.64)
alignment_rows(18.65,2.12,1.35,marker_gaps['>gene2'])
field_text(18.215,.82,'Output of partition schemes:\nNEXUS / RAxML format',color=MUTED)

for label,x,top in [('A',.28,8.65),('B',.28,4.70),('C',3.45,8.65),
                    ('D',7.08,8.65),('E',10.56,8.65),
                    ('F',16.19,8.65),('G',16.19,4.32)]:
    ax.scatter(x,top,s=36**2,facecolors='white',edgecolors=BLACK,lw=1.5,zorder=10,clip_on=False)
    txt(x,top,label,size=FIELD_TITLE_SIZE+4,bold=True,z=11)

# Workflow arrows
arrow(3.02,6.835,3.45,6.835)
arrow(3.02,3.075,3.45,3.075,color=GRAY_STROKE,dashed=True)
arrow(6.65,6.65,7.08,6.65)
arrow(10.13,6.65,10.56,6.65)
arrow(15.76,6.65,16.19,6.65)
arrow(18.215,4.65,18.215,4.32,color=GRAY_STROKE,dashed=True)

# ---- Legend ----
for y,label,fill,dashed in [
    (1.10,'Required',YELLOW,False),
    (.70,'Optional',GRAY,True),
    (.30,'Input / Output',GRAY,False),
]:
    box(.38,y-.15,.46,.30,fill=fill,edge=BLACK,dashed=dashed,r=.10,lw=1.4)
    if label != 'Input / Output':
        arrow(.84,y,1.26,y,color=BLACK,dashed=dashed,ms=14,lw=2.5)
    txt(1.38,y,label,size=FIELD_TEXT_SIZE,bold=True,ha='left')

fig.subplots_adjust(left=.015,right=.985,bottom=.03,top=.985)
for ext in ['png','svg','pdf']:
    fig.savefig(OUT/f'Figure3_WorkflowOverview.{ext}',dpi=220,facecolor='white')
plt.close(fig)
print('Wrote files to',OUT.resolve())

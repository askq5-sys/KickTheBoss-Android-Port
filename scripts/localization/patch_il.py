import sys,os,struct; sys.path.insert(0,os.path.expanduser('~/tools')); from cli import *
SRC=os.path.expanduser('~/w/s42/Assembly-CSharp.dll')
d=bytearray(open(SRC,'rb').read()); a=Asm(bytes(d)); TD=a.typedefs()
def mid(t,m):
    r=[i for n,ms in TD if n==t for i in ms if a.method(i)['name']==m]; return r
def body(t,m,idx=0): return a.body(mid(t,m)[idx])
def ops(b): return {x[0]:(x[2],x[3]) for x in dis(a,b)}
def tok(b,off): return d[b['code']+off+1:b['code']+off+5]
def expect(b,off,name):
    o=ops(b); assert o[off][0].startswith(name), (off,o.get(off),name)
def put(b,start,end,code):
    assert len(code)<=end-start,(len(code),end-start)
    code=code+b'\x00'*(end-start-len(code)); d[b['code']+start:b['code']+end]=code
def ls(n): return bytes([0x11,n])
def ss(n): return bytes([0x13,n])
def ci(n): return bytes([0x1F,n])
def blt(frm_end_off_target): return frm_end_off_target
# 1. LANGUAGE_COUNT = 10
b=body('GHConst','.cctor'); expect(b,0x3c,'ldtoken'); expect(b,0x4d,'stsfld')
put(b,0x3c,0x4d,ci(10))
# 2. boss text: 10 lists
b=body('GameController','CreateAllBossText'); expect(b,0x48,'newobj'); expect(b,0x89,'newarr'); expect(b,0xc6,'br')
LIST=tok(b,0x48); ARR=tok(b,0x89)
code=ci(10)+b'\x8d'+ARR+ss(16)+b'\x16'+ss(21)
L=len(code)
code+=ls(16)+ls(21)+b'\x73'+LIST+b'\xa2'+ls(21)+b'\x17\x58'+ss(21)+ls(21)+ci(10)
code+=b'\x32'+bytes([(L-(len(code)+2))&0xff])
put(b,0x48,0xc6,code)
for off in (0x158,0x1d2,0x215):
    expect(b,off,'ldc.i4.s'); assert d[b['code']+off+1]==9; d[b['code']+off+1]=10
# 3. store items
b=body('GameController','CreateAllStoreItems'); expect(b,0x196,'ldloc.s'); expect(b,0x198,'ldfld'); expect(b,0x1aa,'ldfld'); expect(b,0x2c5,'ldarg.0')
DN=tok(b,0x198); DS=tok(b,0x1aa); I4=tok(b,0x118); TRIM=tok(b,0x1b5) if ops(b)[0x1b5][0]=='callvirt' else None
o=ops(b); trim_off=[k for k,v in o.items() if v[1]=='System.String::Trim'][0]; TRIM=tok(b,trim_off)
ub=ls(7)+b'\xa5'+I4
def col(addc): return ls(4)+ub+b'\x18\x5a'+bytes([addc])+b'\x58\x9a\x6f'+TRIM+b'\xa2'
code=b'\x17\x8c'+I4+ss(7); L=len(code)
code+=ls(8)+b'\x7b'+DN+ub+col(0x1c)
code+=ls(8)+b'\x7b'+DS+ub+col(0x1d)
code+=ub+b'\x17\x58\x8c'+I4+ss(7)+ub+ci(10)
code+=b'\x32'+bytes([(L-(len(code)+2))&0xff])
put(b,0x196,0x2c5,code)
# 4. weapons
b=body('GameController','CreateAllWeaponsInfo'); expect(b,0x1f2,'ldloc.s'); expect(b,0x1f4,'callvirt'); expect(b,0x28a,'ldloc.s')
WN=tok(b,0x1f4); TRIM=tok(b,0x1ff)
code=b'\x17'+ss(4); L=len(code)
code+=ls(11)+b'\x6f'+WN+ls(4)+ls(6)+ls(4)+ci(10)+b'\x58\x9a\x6f'+TRIM+b'\xa2'
code+=ls(4)+b'\x17\x58'+ss(4)+ls(4)+ci(10)+b'\x32'
code+=bytes([(L-(len(code)+1))&0xff])
put(b,0x1f2,0x28a,code)
# 5. hints (counter kept in record.hintIndex, which is set from row[0] after the loop)
b=body('GameController','loadHints'); expect(b,0x98,'ldloc.s'); expect(b,0x9e,'call'); expect(b,0xa3,'stfld'); expect(b,0xaa,'ldfld'); expect(b,0x11e,'ldloc.s')
HD=tok(b,0xaa); HI=tok(b,0xa3); TOI=tok(b,0x9e)
gi=ls(7)+b'\x7b'+HI
code=ls(7)+b'\x16\x7d'+HI; L=len(code)
code+=ls(7)+b'\x7b'+HD+gi+ls(6)+gi+b'\x17\x58\x9a\xa2'
code+=ls(7)+gi+b'\x17\x58\x7d'+HI
code+=gi+ci(10)+b'\x32'
code+=bytes([(L-(len(code)+1))&0xff])
code+=ls(7)+ls(6)+b'\x16\x9a\x28'+TOI+b'\x7d'+HI
put(b,0x98,0x11e,code)
# 6. language panel: iterate 0..9
b=body('HUD','ShowLanguagePanel'); expect(b,0x55,'ldtoken'); expect(b,0x6a,'br'); expect(b,0x6f,'ldloc.1'); expect(b,0x7b,'ldarg.0'); expect(b,0xd7,'ldloc.1'); expect(b,0xe2,'leave')
put(b,0x55,0x6a,b'\x15\x0a\x14\x0b')
put(b,0x6f,0x7b,b'\x06\x17\x58\x0a')
put(b,0xd7,0xe2,b'\x06'+ci(9)+b'\x3f'+struct.pack('<i',0x6f-(0xd7+8)))
# 7. tab label sprites: language 9 -> suffix 'r' (menuWeaponButton_r etc.)
b=body('GameController','ConvertLanguageToShort'); expect(b,0,'ldsfld')
rtok=None
for n_,ms_ in TD:
    for i_ in ms_:
        bb=a.body(i_)
        if not bb: continue
        for x in dis(a,bb):
            if x[2]=='ldstr' and x[3]=="'r'": rtok=d[bb['code']+x[0]+1:bb['code']+x[0]+5]; break
        if rtok: break
    if rtok: break
put(b,0,5,b'\x72'+rtok)

# 8. "ОЦЕНИ!" / "Разработано" only for Russian: the options list has an English and a Russian copy of
#    the Rate button and of the credits line (mainData: GOs 'Bald'/'Dork' and 'Lady'/'Ugly');
#    the hidden one gets scale 0. Code caves: SponsorPayScript::drawTestUI (dead test GUI) holds
#    the update, two stubbed Tapjoy methods hold the hook bodies.
def mtok(t,m):
    return struct.pack('<I',0x06000000|mid(t,m)[0])
def tokof(meth_t,meth_m,pred):
    bb=body(meth_t,meth_m)
    for x in dis(a,bb):
        if pred(x): return d[bb['code']+x[0]+1:bb['code']+x[0]+5]
    raise SystemExit('token not found %s %s'%(meth_t,meth_m))
T_get_transform=tokof('BossController','GetBodyRefs',lambda x:x[3]=='UnityEngine.Component::get_transform') if False else None
def find_tok(name):
    for n_,ms_ in TD:
        for i_ in ms_:
            bb=a.body(i_)
            if not bb: continue
            for x in dis(a,bb):
                if x[3]==name: return d[bb['code']+x[0]+1:bb['code']+x[0]+5]
    raise SystemExit('no '+name)
def find_str(sv):
    for n_,ms_ in TD:
        for i_ in ms_:
            bb=a.body(i_)
            if not bb: continue
            for x in dis(a,bb):
                if x[2]=='ldstr' and x[3]=="'%s'"%sv: return d[bb['code']+x[0]+1:bb['code']+x[0]+5]
    raise SystemExit('no str '+sv)
tGT=find_tok('UnityEngine.Component::get_transform'); tGP=find_tok('UnityEngine.Transform::get_parent')
tFC=find_tok('UnityEngine.Transform::FindChild'); tSLS=find_tok('UnityEngine.Transform::set_localScale')
tONE=find_tok('UnityEngine.Vector3::get_one'); tINST=find_tok('GameController::get_instance')
tSND=None; tBIMS=find_tok('HUD::BringInMenuSound')
bo=body('HUD','BringInOptionsMenu'); o=ops(bo)
# field tokens from HUD code
def fld(meth,name):
    bb=body('HUD',meth)
    for x in dis(a,bb):
        if x[2] in ('ldfld','stfld') and x[3]=='field:'+name: return d[bb['code']+x[0]+1:bb['code']+x[0]+5]
    raise SystemExit('no field '+name)
fOLB=None
for n_,ms_ in TD:
    for i_ in ms_:
        bb=a.body(i_)
        if not bb or fOLB: continue
        for x in dis(a,bb):
            if x[2] in ('ldfld','stfld') and x[3]=='field:optionLanguageButton': fOLB=d[bb['code']+x[0]+1:bb['code']+x[0]+5]; break
            if x[2]=='ldfld' and x[3]=='field:ZERO_VECTOR' and 'fZERO' not in globals(): globals()['fZERO']=d[bb['code']+x[0]+1:bb['code']+x[0]+5]
fZERO=fld('BringInOptionsMenu','ZERO_VECTOR'); fLANG=find_tok('field:playerLanguage')
assert fOLB
code=b''
for name,show_ru in (('Bald',False),('Dork',True),('Lady',False),('Ugly',True)):
    code+=b'\x02\x7b'+fOLB+b'\x6f'+tGT+b'\x6f'+tGP+b'\x72'+find_str(name)+b'\x6f'+tFC
    code+=b'\x28'+tINST+b'\x7b'+fLANG+b'\x1f\x09'
    one=b'\x28'+tONE; zero=b'\x02\x7b'+fZERO
    notru=(zero if show_ru else one); ru_=(one if show_ru else zero)
    # beq.s RU ; <notru> ; br.s SET ; RU: <ru_> ; SET: callvirt set_localScale
    code+=b'\x2e'+bytes([len(notru)+2])+notru+b'\x2b'+bytes([len(ru_)])+ru_+b'\x6f'+tSLS
code+=b'\x2a'
bA=body('SponsorPayScript','drawTestUI'); assert len(code)<=bA['size'],len(code)
d[bA['code']:bA['code']+bA['size']]=code+b'\x00'*(bA['size']-len(code))
tA=mtok('SponsorPayScript','drawTestUI')
bB=body('TapjoyPlugin','ActionComplete'); bC=body('TapjoyPlugin','SetUserID')
codeB=b'\x02\x28'+tBIMS+b'\x02\x28'+tA+b'\x2a'
_bl=[i for i in mid('HUD','ChangeLanguage') if a.body(i)['size']==473][0]; _bl=a.body(_bl); tSND=bytes(d[_bl['code']+0x1cd:_bl['code']+0x1d1]); assert tSND==bytes.fromhex('eb090006'),tSND.hex()
codeC=b'\x1e\x28'+tSND+b'\x02\x28'+tA+b'\x2a'
for bb,cc in ((bB,codeB),(bC,codeC)):
    d[bb['code']:bb['code']+bb['size']]=cc+b'\x00'*(bb['size']-len(cc))
# hooks
expect(bo,0,'ldarg.0'); expect(bo,1,'call'); assert ops(bo)[1][1]=='HUD::BringInMenuSound'
d[bo['code']+1:bo['code']+6]=b'\x28'+mtok('TapjoyPlugin','ActionComplete')
bl=[i for i in mid('HUD','ChangeLanguage') if a.body(i)['size']==473][0]; bl=a.body(bl); ol=ops(bl)
assert ol[0x1cb][0].startswith('ldc.i4.8') and ol[0x1cc][1]=='GHUtility::PlaySound', (ol.get(0x1cb),ol.get(0x1cc))
d[bl['code']+0x1cb:bl['code']+0x1d1]=b'\x02\x28'+mtok('TapjoyPlugin','SetUserID')

# 9. the cave code runs in other classes: make what it touches public (Mono checks member access)
def set_public_method(t,m):
    rows,p0,fmts=a.tab[6]; rs=sum(fmts); idx=mid(t,m)[0]-1
    off=p0+idx*rs+4+2; fl=struct.unpack_from('<H',d,off)[0]; struct.pack_into('<H',d,off,(fl&~7)|6)
def set_public_field(cls,fname):
    TDr=a.tab[2][0]; F=a.tab[4][0]; rows,p0,fmts=a.tab[4]; rs=sum(fmts)
    for i,t in enumerate(TDr):
        if a.str(t[1])==cls:
            fs=t[4]; fe=TDr[i+1][4] if i+1<len(TDr) else len(F)+1
            for j in range(fs,fe):
                if a.str(F[j-1][1])==fname:
                    off=p0+(j-1)*rs; fl=struct.unpack_from('<H',d,off)[0]; struct.pack_into('<H',d,off,(fl&~7)|6); return fl
    raise SystemExit('field '+fname)
set_public_method('HUD','BringInMenuSound')
set_public_method('SponsorPayScript','drawTestUI')
for f_ in ('optionLanguageButton','ZERO_VECTOR'): print(f_, hex(set_public_field('HUD',f_)))
print('playerLanguage', hex(set_public_field('GameController','playerLanguage')))

# 10. the cave keeps none of drawTestUI's locals (their types belong to the removed SponsorPay SDK and
#     made Mono abort while compiling it): local signature 0, no InitLocals.
hb=bA['hdr']; fl=struct.unpack_from('<H',d,hb)[0]
struct.pack_into('<H',d,hb,fl&~0x10); struct.pack_into('<I',d,hb+8,0)
open(sys.argv[1],'wb').write(d); print('written',sys.argv[1])

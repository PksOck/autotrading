# Prostornost, Predlogi in dividendni koledar

Datum: 2026-11-01. Osnova751fe9d. Uporabnik želi izrabo velikega zaslona, nižje uporabne kartice, filtre Predlogov, zložljivo zalogo idej, mesečni/letni dividendni pregled in jasnejše Teze. Izvedba znotraj obstoječega sistema; :3000 ostane nedotaknjen. Uporabnik je izbiro izvedbenih podrobnosti prepustil rootu.

## Izvedbene odločitve

- Tabelarične strani /analysis, /portfolio, /track-record uporabijo razpoložljivo širino; običajne bralne strani obdržijo največ1440px. Analize dobijo različne smiselne privzete širine (identiteta/razlaga širše, številke/datumi ožje); uporabnikovih shranjenih širin ne prepišemo. Na manjših zaslonih drsenje ostane varno, imen/opozoril ne režemo.
- Datum in povezava kartice portfelja sta v isti vrstici. Dnevni denarni/odstotni premik je deterministična **ocena cenovnega premika uvoženih pozicij**, brez gotovine, dnevnega FX in poslov. Denominator so iste količine pri prejšnjem zaključku in isti preverjeni FX. Uvoz še ne hrani ciljne valute FX; zato konsolidiranega dnevnega izida v tuji osnovni valuti ne dovolimo. Kot uporabno nadomestilo prikažemo ločene izvorne valute s svojimi odstotki, izrecno označene kot ocene skupin pozicij. Tudi skupina z manjkajočimi podatki ostane vidna. Valuta pozicije mora ustrezati kotaciji instrumenta. Prikaz zahteva popolne, usklajene pare cen, znano identiteto/FX in pozitivno osnovo; drugače jasna vrzel, ne lažna ničla ali delna vsota. Vir, tržni datumi in datumi količin so dosegljivi.
- Predlogi: URL filter Vsi / V čakanju / V obdelavi / Izvedeni / Potrebna pozornost in iskanje po simbolu/hipotezi. SQL filter pred LIMIT; done z neveljavnim rezultatom spada v pozornost. Povezani globoki zagoni ostanejo ločeno označeni. Filtriranje nikoli ne sproži ponovitve/modela; retry je izrecno dejanje.
- Zaloga idej je native zložljiv razdelek, privzeto zaprt, s številom vrstic in ohranjenimi preferencami. Aktivna watchlista ostane odprta.
- Teze: vseh pet stanj aktivne različice je vidnih tudi pri ničli; pregled stanj ne filtrira trditev ali pending odločitev. Urejanje osnutka in sprejem predlogov ostaneta izrecna. Gre za stanja že zapisanih trditev, ne za skrita finančna merila. Celoviti bralni model BL-226 ostaja ločen.

## Dividendni pregled

Uporabimo ločene kartice mesecev, izbiro leta/valute in seznam instrument/datum/znesek/vir za izbrani mesec. Bruto prejeto in odprti obračuni s pay_date imajo ločeni barvi/legendi; neto samo, če ga vir potrjuje. Letni seštevek ostane po valuti. Zneski se seštevajo v Python Decimal.

Brez izmišljenega urnika: manjkajoči pay_date ostane nerazporejen, ex_date ni dan prejema. Letna ocena trenutnih količin se ne deli z12 in ostane ločena od koledarja. Povezan že knjižen dogodek se ne šteje še enkrat kot odprti prihodek; neskladje zahteva uskladitev, ne samodejne potrditve plačila. Ni združevanja valut ali določitve neta brez davčnih dokazov. Uvoz/coverage/reconciliation in sintetična omejitev pogodbe ostanejo vidni.

Izbrani pristop je koledar iz dokazljivih datumov + ločena letna ocena. Samo kozmetična letna tabela ne odgovori uporabniku; samodejni12-mesečni razrez pa bi ustvaril neresnične datume in zneske. Nov vir objavljenih dividendnih datumov je naslednja podatkovna nadgradnja, ne prikrit fallback.

## Laboratorij: ločen predlog arhitekture

Uporabnik je potrdil oboje, najprej zgodovinske finančne kazalnike, nato pravila nakupa/prodaje. Predlagan nov modul /lab: Zgodovina kazalnikov / Pravila / Primerjave. /track-record še naprej meri izide konkretnih shranjenih mnenj. Podroben podatkovni SPEC laboratorija bo ločen; v tem UX rezu ne ustvarimo navideznega delujočega backtesterja. Potrebujemo čas objave in čas veljavnosti kazalnikov, enote/TTM/forward, restatements, corporate actions in zamrznjene parametre, sicer zgodovinski test lahko vidi podatke iz prihodnosti.

# BL-224: ponovljivo zapiranje pomoči nad predogledom

Dopolnitev po commitu 3e9bee3. Nadaljnji brskalniški test je pod obremenitvijo ponovil zapiranje obeh dialogov tudi po fokusu gumba Zapri. Prvotna diagnoza samo testnega časa zato ni zadostovala; izvirni T1 dokaz ostane zapis takratnega stanja, to poročilo ga glede vzroka dopolnjuje.

V nameščenem Radix DismissableLayer se poslušalec najvišjega dialoga zamenja v useEffect. Pomoč lahko prejme fokus pred to menjavo, zato je lahko za isti Escape še aktiven poslušalec predogleda. Peek zdaj ne dovoli lastnega zapiranja, dokler obstaja odprta označena pomoč. PageHelp obravnava svoj Escape v capture poti tudi ob že preprečenem native defaultu. Oba načina zapiranja uporabita obstoječi idempotentni useBackToClose; ni dodatnega globalnega poslušalca ali neposrednega router posega.

Nov deterministični enotski test najprej RED: že default-prevented Escape pusti pomoč odprto. Po popravku ciljni4/4 in celotni web194/47 datotek PASS. Neodvisni pregled obeh handlerjev skupaj PASS. Dejanski ponovljeni browser tok (odpri pomoč, Nazaj, ponovno odpri, Escape) **20/20**, 10 namiznih in 10 telefonskih ponovitev. Končni celotni browser **90 passed / 10 namernih device-specific skipov**, 100 primerov.

Samo demo web :3100, brez podatkovnih sprememb, :3000 se ne spreminja. Metodne API/UI dopolnitve BL-228 imajo ločen dokaz in commit.

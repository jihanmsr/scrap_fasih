#!/bin/bash
echo "[" > /Users/jihanmaisaroh/scrap_fasih/fast_results.json
for i in {0..10}; do
  echo "Fetching page $i..."
  curl -s 'https://fasih-sm.bps.go.id/app/api/analytic/api/v2/assignment/report-progress-by-responsibility' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7' \
  -H 'content-type: application/json' \
  -b 'f5avraaaaaaaaaaaaaaaa_session_=EMIDPDLBICKKCPFEMHIIEIKODHHOGIMEAKFHLHHMHEPKGENCDDOKDJPBMKJLGIEEDPKDLNOEJANNEKFGICDAAHCBIAIICCINKEIACJNMLNBNGIGMLENEDFJPBOIDIHCB; f5_cspm=1234; f5avraaaaaaaaaaaaaaaa_session_=LEJHDNLAGBFNBIADCPDOHOFNHHMLODCMAELCMBGDJLOMKIFGGHENANINHFDLIJNJNFGDKPHFEHOHHPCHEGGAEHNNLPFNLAIJCFFFAJNLJEJCKFJLOPCOFKFJEDEHEEHM; db8ca2b43ed851cc93e71fd5fd72bff7=13b6ee7a488307959e12f96ea563eca4; XSRF-TOKEN=c406ff8c-a60b-4c5f-90fa-998f55393663; SESSION=bcc86f50-4d70-4ee2-9549-56b09659236e; TS0151fc2b=0167a1c86110e7c1289903edf20d57c3badced1a3b46c05045cc89f96c188a2b424b3155dbdfbce8e1f195d60f0569c5109c93fb37; TS00000000076=0868f8be6fab2800fabe5333cc501bd511faa90f10c3802f393636edab2770a383a9316f5e5ad2c518062d300aece7b608920af3c109d000a8a24e98cdecabd98c4bdf1f3dedcc8b3d312420ea1e46954fabfb26f958870e0b310e51f954932c8a18d56d6c6bd8b0e86b96ee371d233817d2fbb213fd127a8131afd094f240dfab93664edb7cd302b531bc9dcd0a2d66ff8ea5234ff88bea72fcc9e29e2c7df71372677cbefb677f79c4679b9847c136088f514880d8510b745db0595b8032e590a3e060ce38a2fb11ec73a0cb6b9a9a5c624bcb091458fd3c8db6222ae95fd1362ebe823669b2085dc96463a77c78566f81ce68a2ddff4deb1dd2c6e20e339c155e05742a4a1c5a; TSPD_101_DID=0868f8be6fab2800fabe5333cc501bd511faa90f10c3802f393636edab2770a383a9316f5e5ad2c518062d300aece7b608920af3c1063800d6b9499565cf38d946e48195d8a5ecaab667fcb89a04a19617c67e75c059da206f9883d6047bf90cb6e5bc4cb7e89f69a399368cf8810b07; TS011f2d1a=01266d26d06487d5323728116ed2786681f3017f92805f52884a4b344f0c8c9e83542aefc1a76f52b2d17b612843309dbc5c527955; TSPD_101=0868f8be6fab2800f12f2da3edbdeccaeaf2bfe2caa6a0e81fc9d70b85adac724a5741a2ae6458c69266cf0de23eefed08183f1000051800df63a6fe7565d0695ca1732140a3428bba23ce13beb1c95e; f5avraaaaaaaaaaaaaaaa_session_=IJNMMAGMFBGCEIFOAPOLJPNJMIHEFJHOEBNCIEJNEAPDKPKDBCPHFOAELCBDGCHMGICDBHIOCAHFBLNLOEPADOKDJANELNLFAGENGOHIHOEINHLPAIFKJMJMADAGOALM; TS5220f739077=0868f8be6fab280098b7f2a1a1fab02d2840b01631acc75a7006a4d99740d8e123b885ec30ba598956b1aa9a52f7357408a6145afa17200017b44c1a06fdeb47cae27282805de1b24d3659455468905ff4828e0ac5d02871; TS5220f739029=0868f8be6fab280059bce6c564ac8a06422d1b3959f5e97c9074ecd011a0eeb38431733ca1bb5e24bd807ef1fde3eabd; TSf1edb2d2027=0868f8be6fab2000f3236ff72991eff258fb774369bc87e0e60e2e8cf6775abb5abff9c23e2bb1fe086b1e4ad81130009e373eaade8ef0ab3d25e779e046605564e5de4be702039c0d7de0224e7d6bf5ced18bbb0bed147d75ea623edbfa32b0' \
  -H 'origin: https://fasih-sm.bps.go.id' \
  -H 'priority: u=1, i' \
  -H 'sec-ch-ua: "Google Chrome";v="149", "Chromium";v="149", "Not)A;Brand";v="24"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/149.0.0.0 Safari/537.36' \
  -H 'x-xsrf-token: c406ff8c-a60b-4c5f-90fa-998f55393663' \
  --data-raw '{"surveyPeriodId":"fd68e454-ba45-4b85-8205-f3bf777ded24","surveyRoleId":"6d7d919a-45e5-4779-bb87-2905b49fd31a","size":100,"page":'$i',"search":"","target":"TARGET_ONLY","region":{"region1Id":"5214ecb2-bef1-4a86-9446-451cf430928e","region2Id":"4ab6ca2f-7952-4e8e-a94d-b6dd933e5d44","region3Id":"c3a96057-476b-4a0e-b08b-c5143d46ecfd","region4Id":null,"region5Id":null,"region6Id":null,"region7Id":null,"region8Id":null,"region9Id":null,"region10Id":null},"regionSummaryLevel":6}' >> /Users/jihanmaisaroh/scrap_fasih/fast_results.json
  echo "," >> /Users/jihanmaisaroh/scrap_fasih/fast_results.json
done
echo "]" >> /Users/jihanmaisaroh/scrap_fasih/fast_results.json

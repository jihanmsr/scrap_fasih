const https = require('https');
const fs = require('fs');

const MAX_RETRIES = 3;
let allData = [];
let start = 0;
const length = 1000;

const cookie = 'f5avraaaaaaaaaaaaaaaa_session_=AKODOECAMEAEEKKDGFJCMKDGMEPAJBDDPGEHBEFLBPNGDPIJKDFGJOONNGOHECDIDPEDDMLBENDEBBAGAFMACANLDFKLMJFPMFHMNODBKJLCAFIGLDILHLOOJEBFKDKM; f5avraaaaaaaaaaaaaaaa_session_=MLAJLNMGDHOFEJHKAHEEODCEJJELHHBNLJNMLCMMHOLFDJJEFOAFCIEOPBLHCCPNHHCDCBEFIHDGNONGHHOAOMOHDEHKONKFKLGEGHKMJCGLPNIIMJHJIIJGMHJIOKBB; db8ca2b43ed851cc93e71fd5fd72bff7=36131fa44353feb388ca15ca1d926e37; XSRF-TOKEN=17f3c068-ef6a-40f4-b1a8-352fbb377bd3; SESSION=0a69d09b-cccd-4b50-a9d2-ac7c2551385a; TS0151fc2b=0167a1c861ffd2b6ebd8f1dab25c29a207d84ffca38ec4e23029cb8322d936d3f0aaba9617118a918b3399b6dc125a92b4e3e3575d; TS00000000076=0868f8be6fab28006017dce7c11d5489264df1df31d4e1a7675fb57e45dc04e9b4f892c769ee9d0767966e77f35ba6c1081842a6e909d0003d653712774bfb13329be1c5ae483f829a4a04281e9c9dbd9b1457326616d51a656eb6ce84027d0f8f9dbd8b579e0ace783988d340ac8c8548be3fe715d58123e6c7b087f42f46414e6c76137bd50295c3c91ab41850b600fc4550ea2974dc7c12bc5c419158f5e4a1ac206f1cbdaa8edd8726210bdffc9d84913c49338e5134a38caf2d7a7b43f2a9588ca7a645f0ac0b64155d3f54bd470ade95d312dc0a9e093eedd974d215eb858a0aeccf709e0b64fe7b8e9754db3b35aa1c3b609505aefbf338656bae9799f709329f8f733a08; TSPD_101_DID=0868f8be6fab28006017dce7c11d5489264df1df31d4e1a7675fb57e45dc04e9b4f892c769ee9d0767966e77f35ba6c1081842a6e9063800e1b6b01a0e4fe312b5c161e11ee81864cd648547f131fdd9eb2dd5c67fcf83d079da5ecf123696b4683bb395c8f92da89c23b139649e01c1; TS011f2d1a=01266d26d04d07af4ba410b1d57ac3428993b38ca3de5d2c52acb4ad837de4ca945c76d392b9abdd09d55f92e26fffc9a53fd28c52; TSPD_101=0868f8be6fab2800875893cfb53a30fc1b513e43dc376a84c09a5bc3fcb8280e39d2f6cae5eb3a4a20f8460dd0dd0cae08e4472be50518007f7325ccc7cf27d25ca1732140a3428bba23ce13beb1c95e; TS5220f739077=0868f8be6fab28006393b944a9b59d441f1e1d040ee9fca1aa2974ad85de233ca27daf8dd956b9cb2f67a690f36a4a5a080da3641d17200008d6a12aee58b17d88d84eafbdcb9669b930b9fcb9fe302d1a638ca0b097c3fa; TS5220f739029=0868f8be6fab28008f8328804ff4b384a4bff80d48261e36bcf7bb0c9fca8525b77547ccf24b6c559474f33d73b579af; TSf1edb2d2027=0868f8be6fab2000c8a105f95fe0c83aae227c616f0d8dccbe9cb8672c4974cc376fcf2186adbdd708379d16c511300023adb27cb15371d6cc74fa6b235a9aff4b2400545eff3844cea2a60b1ead452c436cbe9ba893414703d966cd42393082';
const xsrf = '17f3c068-ef6a-40f4-b1a8-352fbb377bd3';

function fetchPage(retryCount = 0) {
  const data = JSON.stringify({
    "start": start,
    "length": length,
    "columns": [
      {"data":"id","orderable":true},
      {"data":"codeIdentity","orderable":true},
      {"data":"data1","orderable":true},
      {"data":"data2","orderable":true},
      {"data":"data3","orderable":true},
      {"data":"data4","orderable":true},
      {"data":"data5","orderable":true},
      {"data":"data6","orderable":true},
      {"data":"data7","orderable":true},
      {"data":"data8","orderable":true},
      {"data":"data9","orderable":true},
      {"data":"data10","orderable":true}
    ],
    "order": [],
    "search": {"value":"","regex":false},
    "assignmentExtraParam": {
      "region1Id": "5214ecb2-bef1-4a86-9446-451cf430928e",
      "region2Id": "bc32354f-1245-426f-b2cf-a5733e1295ad",
      "surveyPeriodId": "fd68e454-ba45-4b85-8205-f3bf777ded24",
      "assignmentErrorStatusType": -1,
      "filterTargetType": "TARGET_ONLY"
    }
  });

  const options = {
    hostname: 'fasih-sm.bps.go.id',
    port: 443,
    path: '/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode',
    method: 'POST',
    headers: {
      'accept': '*/*',
      'accept-language': 'en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7',
      'content-type': 'application/json',
      'cookie': cookie,
      'origin': 'https://fasih-sm.bps.go.id',
      'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36',
      'x-xsrf-token': xsrf,
      'Content-Length': Buffer.byteLength(data)
    }
  };

  const req = https.request(options, (res) => {
    let body = [];
    res.on('data', (chunk) => body.push(chunk));
    res.on('end', () => {
      body = Buffer.concat(body).toString();
      try {
        const j = JSON.parse(body);
        const records = j.searchData || [];
        allData.push(...records);
        console.log(`Fetched \${records.length} records. Total so far: \${allData.length}`);
        
        if (records.length === 0) {
          console.log('Finished fetching all data. Writing to file...');
          fs.writeFileSync('bangkep_data.json', JSON.stringify(allData, null, 2));
          console.log(`Saved \${allData.length} records to bangkep_data.json`);
        } else {
          start += length;
          fetchPage(0);
        }
      } catch (err) {
        console.error('Error parsing JSON on start', start, ':', err.message);
        if (retryCount < MAX_RETRIES) {
          console.log('Retrying start', start, '...');
          fetchPage(retryCount + 1);
        } else {
          console.log('Failed after max retries.');
          fs.writeFileSync('bangkep_data_partial.json', JSON.stringify(allData, null, 2));
        }
      }
    });
  });

  req.on('error', (error) => {
    console.error(error);
    if (retryCount < MAX_RETRIES) {
      console.log('Retrying...');
      fetchPage(retryCount + 1);
    } else {
      console.log('Failed after max retries.');
    }
  });

  req.write(data);
  req.end();
}

console.log('Starting data fetch...');
fetchPage();

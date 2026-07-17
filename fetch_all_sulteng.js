const https = require('https');
const fs = require('fs');

const cookie = 'f5avraaaaaaaaaaaaaaaa_session_=PGIOPNKFFHBNENIMGNGBMFMCJEDHPAEKDJOOCNCDMNMKJOEDIBMBCAOLDMOPMNNIDHIDJGNIEKDFFELONFJACNLAIGGJNGNPEAHCJEJGJCBOLMHPNODCAPGKKIABIONF; db8ca2b43ed851cc93e71fd5fd72bff7=36131fa44353feb388ca15ca1d926e37; XSRF-TOKEN=17f3c068-ef6a-40f4-b1a8-352fbb377bd3; SESSION=0a69d09b-cccd-4b50-a9d2-ac7c2551385a; TS0151fc2b=0167a1c861ffd2b6ebd8f1dab25c29a207d84ffca38ec4e23029cb8322d936d3f0aaba9617118a918b3399b6dc125a92b4e3e3575d; f5avraaaaaaaaaaaaaaaa_session_=MLJLDPNAIJLFPADGKNDDADAICOPBDMNKJKIDBIGLJKAFFJMLANFAMBJBKDBPCLGKMEMDGDKPFAJJGMCHFKLANGEIAGIHCKCEPOGMJFPMDGNLGNIJKDAHNJPKNPGKDKGB; TS00000000076=0868f8be6fab28006c8eabb58607ce43750d46451f570fa101c11cc98ff1fa652d8763be6944eece717cf142b504432e08561f72fa09d0007fa63b21f679f23fccfeac722ac280eb93b08aeac6a8bef06b9d5369f203126d4bd14a3ccbdbf8dd9ccb58d62860be561fce852787c7afd27950481b5095ea8d914f2e1e3d60bcba2ae9452fb583e97e6855fc5f49c002ea51849796ed95a46023728fed5b2032f4c6661cbf10e388c45d2a5518c56de6475a4e6d63276ff1589ff89c25dc2d53dde778923063eab3244a814b551e1ce69064bcf3a79c076949c66685281cdfd7da602aa11087e0d7752ab37e400c5e8819fa195caab2d29a5d1cfdea5a47417e13622e07afdf4a1ba0; TSPD_101_DID=0868f8be6fab28006c8eabb58607ce43750d46451f570fa101c11cc98ff1fa652d8763be6944eece717cf142b504432e08561f72fa0638006d864d55edeaf0b5b5feb59ae8c3a919019f122591d6ea6e62298fa81348e55fc1c0fcdac9687904d847d709789cf353a377623d02981ecc; TS011f2d1a=01266d26d0d98210f81e9cb5b478918481f0a1b18061803cff277faeacb35b7d923b518fe5e76e3d84dec41577ab332252f008f591; TSPD_101=0868f8be6fab2800cf8581696d8963599c83e6c5d8896af0c4df6f25762bcfb89629346bd1d13cc26c29c97ab05ef2ae08c7a0c892051800284c51ce471222ae5ca1732140a3428bba23ce13beb1c95e; TS5220f739077=0868f8be6fab2800b7f76d30d3d2975361851cc6e17ce0c07473f25f78aa2f8f5e8dafe7151eb36eb3e57ae819599a5a0834c2409f172000f08eced18878e48bee32ead77270abd06b121a344efdcb4416b0cc01a2f83077; TS5220f739029=0868f8be6fab28002304fccaa03790b01deff3d7e8c8991588cbbd45dd246aa5646bfb6b693264bd47aa0bbad4d8605e; TSf1edb2d2027=0868f8be6fab200088355759ae37585e4ce2f2d080fc22798c7d3b3a3f355005b8f7de4e16d746cd0877826853113000a736b83f9ff5da8f61c9c004a70ff95070fc2c997aaac785db627d39eed2c55b31be011e2a608d8f0a7686d676fd5d7c';
const xsrf = '17f3c068-ef6a-40f4-b1a8-352fbb377bd3';

const SUMBER = ['DTSEN', 'UMK', 'UMKM', 'NONBKU', 'DUMMY'];
const streams = {};
SUMBER.forEach(s => {
  streams[s] = fs.createWriteStream(__dirname + `/api_data_${s.toLowerCase()}.csv`);
  streams[s].write('uuid,kode_identitas,kabkot\n');
});

const summary = {};
let totalFetched = 0;
let totalSaved = 0;

let start = 0;
const length = 5000;
const MAX_RETRIES = 5;

function fetchPage(retryCount = 0) {
  const data = JSON.stringify({
    start,
    length,
    columns: Array(12).fill(0).map((_, i) => ({ data: i===0?"id":i===1?"codeIdentity":`data${i-1}`, orderable: true })),
    order: [],
    search: { value: "", regex: false },
    assignmentExtraParam: {
      region1Id: "5214ecb2-bef1-4a86-9446-451cf430928e",
      surveyPeriodId: "fd68e454-ba45-4b85-8205-f3bf777ded24",
      assignmentErrorStatusType: -1,
      filterTargetType: "TARGET_ONLY"
    }
  });

  const options = {
    hostname: 'fasih-sm.bps.go.id',
    port: 443,
    path: '/app/api/analytic/api/v2/assignment/datatable-all-user-survey-periode',
    method: 'POST',
    headers: {
      'accept': '*/*',
      'content-type': 'application/json',
      'cookie': cookie,
      'user-agent': 'Mozilla/5.0',
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
        totalFetched += records.length;
        console.log(`[API] Fetched ${records.length} records. Total fetched: ${totalFetched} / ${j.recordsTotal || '?'}`);
        
        // Process records
        records.forEach(r => {
          const uuid = r.id;
          const str = r.codeIdentity;
          if (!str) return;
          const kabkot = str.substring(0, 4);
          
          const parts = str.split(' - ').map(p => p.trim());
          if (parts.length >= 3) {
            const middle = parts[1].toUpperCase();
            if (SUMBER.includes(middle)) {
              // escape quotes
              const safeName = str.replace(/\"/g, '\"\"');
              streams[middle].write(`${uuid},"${safeName}",${kabkot}\n`);
              
              if (!summary[kabkot]) summary[kabkot] = { DTSEN: 0, UMK: 0, UMKM: 0, NONBKU: 0, DUMMY: 0 };
              summary[kabkot][middle]++;
              totalSaved++;
            }
          }
        });

        if (records.length === 0 || records.length < length) {
          console.log('Finished fetching all data from API!');
          SUMBER.forEach(s => streams[s].end());
          
          // Write summary
          const sumStream = fs.createWriteStream(__dirname + '/api_summary_sumber.csv');
          sumStream.write('kabkot,DTSEN,UMK,UMKM,NONBKU,DUMMY,Total\n');
          
          let sums = { DTSEN: 0, UMK: 0, UMKM: 0, NONBKU: 0, DUMMY: 0, Total: 0 };
          for (const kab in summary) {
            const row = summary[kab];
            const sum = row.DTSEN + row.UMK + row.UMKM + row.NONBKU + row.DUMMY;
            sumStream.write(`${kab},${row.DTSEN},${row.UMK},${row.UMKM},${row.NONBKU},${row.DUMMY},${sum}\n`);
            sums.DTSEN += row.DTSEN; sums.UMK += row.UMK; sums.UMKM += row.UMKM;
            sums.NONBKU += row.NONBKU; sums.DUMMY += row.DUMMY; sums.Total += sum;
          }
          sumStream.write(`TOTAL SULTENG,${sums.DTSEN},${sums.UMK},${sums.UMKM},${sums.NONBKU},${sums.DUMMY},${sums.Total}\n`);
          sumStream.end();
          
          console.log(`Saved ${totalSaved} valid records across all sumber.`);
        } else {
          start += length;
          fetchPage(0);
        }
      } catch (err) {
        console.error('Error parsing JSON on start', start, ':', err.message);
        if (retryCount < MAX_RETRIES) {
          console.log('Retrying start', start, '...');
          setTimeout(() => fetchPage(retryCount + 1), 2000);
        } else {
          console.log('Failed after max retries.');
          SUMBER.forEach(s => streams[s].end());
        }
      }
    });
  });

  req.on('error', (error) => {
    console.error(error);
    if (retryCount < MAX_RETRIES) {
      console.log('Retrying...');
      setTimeout(() => fetchPage(retryCount + 1), 2000);
    } else {
      console.log('Failed after max retries.');
    }
  });

  req.write(data);
  req.end();
}

console.log('Starting data fetch from API...');
fetchPage();

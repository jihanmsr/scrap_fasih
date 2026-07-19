function updateCountdownSE2026(belumSelesai) {
    const countdownDaysEl = document.getElementById('countdown-days');
    const countdownTargetEl = document.getElementById('countdown-daily-target');
    if (!countdownDaysEl || !countdownTargetEl) return;
    
    // Asumsi tgl akhir 31 Agustus 2026
    const endDate = new Date('2026-08-31T00:00:00');
    let today = new Date(); // Atau gunakan tanggal dashboard jika diperlukan
    today.setHours(0, 0, 0, 0);
    
    let remainingWorkingDays = 0;
    
    if (today <= endDate) {
        let curDate = new Date(today);
        while (curDate <= endDate) {
            if (curDate.getDay() !== 0) { // Bukan hari Minggu
                remainingWorkingDays++;
            }
            curDate.setDate(curDate.getDate() + 1);
        }
    }
    
    if (remainingWorkingDays > 0) {
        countdownDaysEl.textContent = `${remainingWorkingDays} Hari`;
        const targetPerDay = Math.ceil(belumSelesai / remainingWorkingDays);
        countdownTargetEl.textContent = targetPerDay.toLocaleString('id-ID');
    } else {
        countdownDaysEl.textContent = '0 Hari';
        countdownTargetEl.textContent = '0';
    }
}

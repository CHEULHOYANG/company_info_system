// 페이지가 로드될 때 실행될 함수들
document.addEventListener('DOMContentLoaded', () => {
    const searchButton = document.getElementById('search-button');
    const companyNameInput = document.getElementById('company-name-input');
    const bizNoInput = document.getElementById('biz-no-input');

    // 검색 버튼 클릭 이벤트
    searchButton.addEventListener('click', () => {
        performSearch();
    });

    // 엔터 키 입력으로 검색 실행
    companyNameInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            performSearch();
        }
    });

    bizNoInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter') {
            performSearch();
        }
    });

    // 페이지 로드 시 전체 목록 조회
    fetchCompanies('', '');
});

// 검색 실행 함수
function performSearch() {
    const companyName = document.getElementById('company-name-input').value;
    const bizNo = document.getElementById('biz-no-input').value;
    fetchCompanies(companyName, bizNo);
}


// 백엔드 API에 기업 정보를 요청하는 함수
async function fetchCompanies(companyName, bizNo) {
    const tableBody = document.getElementById('results-table-body');
    tableBody.innerHTML = '<tr><td colspan="8" style="text-align:center;">데이터를 불러오는 중...</td></tr>';

    // API 요청 URL 생성 (쿼리 파라미터 추가)
    const url = `/api/companies?company_name=${encodeURIComponent(companyName)}&biz_no=${encodeURIComponent(bizNo)}`;

    try {
        const response = await fetch(url);
        const companies = await response.json();
        displayResults(companies);
    } catch (error) {
        console.error('데이터를 가져오는 데 실패했습니다:', error);
        tableBody.innerHTML = '<tr><td colspan="8" style="text-align:center;">데이터를 불러오는 데 실패했습니다.</td></tr>';
    }
}

// 검색 결과를 테이블에 표시하는 함수
function displayResults(companies) {
    const tableBody = document.getElementById('results-table-body');
    tableBody.innerHTML = ''; // 기존 내용을 비웁니다.

    if (companies.length === 0) {
        tableBody.innerHTML = '<tr><td colspan="8" style="text-align:center;">검색 결과가 없습니다.</td></tr>';
        return;
    }

    companies.forEach(company => {
        const row = document.createElement('tr');
        
        // 숫자에 콤마 추가하는 헬퍼 함수
        const formatNumber = (num) => num ? num.toLocaleString() : 'N/A';

        row.innerHTML = `
            <td>${company.biz_no || 'N/A'}</td>
            <td>${company.company_name || 'N/A'}</td>
            <td>${company.representative_name || 'N/A'}</td>
            <td>${company.company_size || 'N/A'}</td>
            <td>${company.region || 'N/A'}</td>
            <td>${company.industry_name || 'N/A'}</td>
            <td style="text-align:right;">${formatNumber(company.sales_revenue)}</td>
            <td style="text-align:right;">${formatNumber(company.retained_earnings)}</td>
        `;
        tableBody.appendChild(row);
    });
}
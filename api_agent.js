const http = require('http')

const base = 'http://localhost:5000/api/v1'

count = 0

let functions = [
    get_latest_trade,
    get_best_bid,
    get_best_ask,
    get_midprice,
    get_order_book,
    get_quotes,
    get_trades
]

function hammer() {
    const start = Date.now()
    let runs = 100
    let run = 0
    while (run < runs) {
        if(run >= runs) break
        run += 1
        setTimeout(() => {
            functions[Math.floor(Math.random() * functions.length)]()
        }, 100)
    }
    const end = Date.now()
    console.log(count, end - start)
}

// make get request to api
function make_request(url) {
    http.get(url, response => {
        let body = ''
        response.on('data', data => {
            body += data.toString()
        })

        response.on('end', () => {
            const profile = JSON.parse(body)
            // console.log(url, profile)
            count += 1
        })
    }
    )
}


function get_latest_trade(ticker='XYZ') {
    const url =  `${base}/get_latest_trade?ticker=${ticker}`
    make_request(url)
}

function get_best_bid(ticker='XYZ') {
    const url =  `${base}/get_best_bid?ticker=${ticker}`
    make_request(url)
}

function get_best_ask(ticker='XYZ') {
    const url =  `${base}/get_best_ask?ticker=${ticker}`
    make_request(url)
}

function get_midprice(ticker='XYZ') {
    const url =  `${base}/get_midprice?ticker=${ticker}`
    make_request(url)
}

function get_order_book(ticker='XYZ') {
    const url =  `${base}/get_order_book?ticker=${ticker}`
    make_request(url)
}

function get_quotes(ticker='XYZ') {
    const url =  `${base}/get_quotes?ticker=${ticker}`
    make_request(url)
}

function get_trades(ticker='XYZ') {
    const url =  `${base}/get_trades?ticker=${ticker}`
    make_request(url)
}


hammer()
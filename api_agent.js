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
    let runners = []
    while (run < runs) {
        if(run >= runs) break
        run += 1
        runners.push(new Promise(resolve => setTimeout(() => {
            functions[Math.floor(Math.random() * functions.length)](resolve)
        }, 100) ) )
    }

    Promise.all(runners).then(() => {
        const end = Date.now()
        console.log(count, end - start)
    })
}

// make get request to api
function make_request(url, resolve) {
    http.get(url, response => {
        let body = ''
        response.on('data', data => {
            body += data.toString()
        })

        response.on('end', () => {
            let response = JSON.parse(body)
            resolve(response)
            count += 1
        })
    }
    )
}


function get_latest_trade(resolve) {
    const url =  `${base}/get_latest_trade?ticker=XYZ`
    make_request(url, resolve)
}

function get_best_bid(resolve) {
    const url =  `${base}/get_best_bid?ticker=XYZ`
    make_request(url, resolve)
}

function get_best_ask(resolve) {
    const url =  `${base}/get_best_ask?ticker=XYZ`
    make_request(url, resolve)
}

function get_midprice(resolve) {
    const url =  `${base}/get_midprice?ticker=XYZ`
    make_request(url, resolve)
}

function get_order_book(resolve) {
    const url =  `${base}/get_order_book?ticker=XYZ`
    make_request(url, resolve)
}

function get_quotes(resolve) {
    const url =  `${base}/get_quotes?ticker=XYZ`
    make_request(url, resolve)
}

function get_trades(resolve) {
    const url =  `${base}/get_trades?ticker=XYZ`
    make_request(url, resolve)
}


hammer()
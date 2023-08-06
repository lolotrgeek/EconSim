import zmq from 'zeromq'

export default class Requester {
    constructor(channel = '5570') {
        this.channel = channel
        this.socket = new zmq.Request
        this.socket.connect(`tcp://127.0.0.1:${this.channel}`)
        this.queue = []
        this.processing = false
        this.latest_result = {}
        this.debug = false
    }

    async request_direct(topic, msg) {
        try {
            msg.topic = topic
            this.socket.send(JSON.stringify(msg))
            const reply = await this.socket.receive()
            return JSON.parse(reply)
        } catch (e) {
            console.log("[Requester Error]", e, "Request:", msg)
            return { topic, error: e.message }
        }
    }

    async request(topic, msg) {
        this.queue.push({ topic, msg })
        this.processQueue()
    }

    parser(reply) {
        try {
            return JSON.parse(reply)
        } catch (Parse_error) {
            try {
                return reply.toString()
            } catch (error) {
                return { error: "cannot parse reply"}
            }
        }
        
    }

    async processQueue() {
        if (this.processing) return
        this.processing = true

        while (this.queue.length > 0) {
            const { topic, msg } = this.queue.shift()
            try {
                msg.topic = topic
                this.socket.send(JSON.stringify(msg))
                if (this.debug) {console.log("Received response for topic:", topic)}
                const reply = await this.socket.receive()
                this.latest_result = this.parser(reply)
            } catch (e) {
                console.log("[Requester Error]", e, "Request:", msg)
            }
        }

        this.processing = false
    }
}
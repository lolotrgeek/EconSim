import zmq from 'zeromq'

export default class Subscriber {
    constructor(channel = '5572') {
        this.channel = channel
        this.socket = new zmq.Subscriber
        this.socket.connect(`tcp://127.0.0.1:${this.channel}`)
        this.latest_reply = {}
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

    async subscribe(topic) {
        this.socket.subscribe(topic)
        for await (const [topic, msg] of this.socket) {
            this.latest_reply = this.parser(msg)
          }
    }

    async pull(topic) {
        this.socket.subscribe(topic)
        const [topic, msg] = await this.socket.receive()
        this.latest_reply = this.parser(msg)
        return this.latest_reply
    }
    
}

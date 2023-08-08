import zmq from 'zeromq'

export default class Puller {
    constructor(channel = '5571') {
        this.channel = channel
        this.socket = new zmq.Pull
        this.socket.conflate = true
        this.socket.connect(`tcp://127.0.0.1:${this.channel}`)
        this.latest_result = {}
    }


    parser(reply) {
        try {
            return JSON.parse(reply)
        } catch (Parse_error) {
            try {
                return reply.toString()
            } catch (error) {
                return { error: "cannot parse reply" }
            }
        }

    }

    async pull(topic) {
        try {
            const raw_msg = await this.socket.receive()
            let msg = this.parser(raw_msg)
            if(typeof msg === 'object' && topic in msg) this.latest_result = msg[topic]
            else this.latest_result = { error: "no such topic"}
        } catch (e) {
            console.log("[Puller Error]", e)
            return { error: e.message }
        }
    }
}
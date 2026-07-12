class WebSocketClient {
  constructor(url) {
    this.url = url
    this.ws = null
    this.reconnectAttempts = 0
    this.maxReconnectAttempts = 5
    this.callbacks = {}
    this.connected = false
  }

  connect() {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        this.connected = true
        this.reconnectAttempts = 0
        this._trigger('open')
        resolve()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this._trigger('message', data)
        } catch (e) {
          this._trigger('message', event.data)
        }
      }

      this.ws.onerror = (error) => {
        this._trigger('error', error)
        reject(error)
      }

      this.ws.onclose = () => {
        this.connected = false
        this._trigger('close')
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          setTimeout(() => {
            this.reconnectAttempts++
            this.connect()
          }, 2000 * this.reconnectAttempts)
        }
      }
    })
  }

  send(data) {
    if (this.ws && this.connected) {
      this.ws.send(JSON.stringify(data))
    }
  }

  on(event, callback) {
    if (!this.callbacks[event]) {
      this.callbacks[event] = []
    }
    this.callbacks[event].push(callback)
  }

  off(event, callback) {
    if (this.callbacks[event]) {
      this.callbacks[event] = this.callbacks[event].filter((cb) => cb !== callback)
    }
  }

  _trigger(event, data) {
    if (this.callbacks[event]) {
      this.callbacks[event].forEach((cb) => cb(data))
    }
  }

  close() {
    if (this.ws) {
      this.ws.close()
    }
    this.connected = false
  }
}

export default WebSocketClient

import { Controller } from 'stimulus';
import ReconnectingWebSocket from 'reconnecting-websocket';

import { connectStreamSource, disconnectStreamSource } from '@hotwired/turbo';

export default class extends Controller {
  static values = {
    url: String,
  };

  connect() {
    const protocol = window.location.protocol == 'https:' ? 'wss' : 'ws';
    const url = protocol + '://' + window.location.host + this.urlValue;
    this.source = new ReconnectingWebSocket(url);
    connectStreamSource(this.source);
  }

  disconnect() {
    disconnectStreamSource(this.source);
    if (this.socket) {
      this.socket.close();
    }
    this.source = null;
  }
}

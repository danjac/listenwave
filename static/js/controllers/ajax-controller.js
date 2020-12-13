import axios from 'axios';
import Turbolinks from 'turbolinks';
import { Controller } from 'stimulus';
import debounce from 'lodash.debounce';
import throttle from 'lodash.throttle';

export default class extends Controller {
  static targets = ['fragment'];
  static values = {
    confirm: String,
    redirect: String,
    remove: Boolean,
    replace: Boolean,
    url: String,
    throttle: Number,
    debounce: Number,
  };

  initialize() {
    if (this.hasDebounceValue) {
      this.sendAjax = debounce(this.sendAjax, this.debounceValue).bind(this);
    }
    if (this.hasThrottleValue) {
      this.sendAjax = throttle(this.sendAjax, this.throttleValue).bind(this);
    }
  }

  get(event) {
    event.preventDefault();
    this.sendAjax('GET');
  }

  post(event) {
    event.preventDefault();
    this.sendAjax('POST');
  }

  put(event) {
    event.preventDefault();
    this.sendAjax('POST');
  }

  delete(event) {
    event.preventDefault();
    this.sendAjax('DELETE');
  }

  async sendAjax(method) {
    if (this.hasConfirmValue && !window.confirm(this.confirmValue)) {
      return;
    }

    const url = this.urlValue || this.element.getAttribute('href');

    const headers = {
      'Turbolinks-Referrer': location.href,
    };

    // request server return an HTML fragment to insert into DOM
    //
    if (this.hasReplaceValue) {
      headers['X-Request-Fragment'] = true;
    }

    const response = await axios({
      headers,
      method,
      url,
    });

    if (this.hasRedirectValue) {
      if (this.redirectValue !== 'none') Turbolinks.visit(this.redirectValue);
      return;
    }

    // remove target
    if (this.hasRemoveValue) {
      if (this.hasFragmentTargets) {
        this.fragmentTargets.forEach((target) => target.remove());
      } else {
        this.element.remove();
      }
      return;
    }

    const contentType = response.headers['content-type'];

    if (this.hasReplaceValue && contentType.match(/html/)) {
      if (this.hasFragmentTargets) {
        this.fragmentTargets.forEach((target) => (target.innerHTML = response.data));
      } else {
        this.element.innerHTML = response.data;
      }
      return;
    }

    // default behaviour: redirect passed down in header
    if (contentType.match(/javascript/)) {
      /* eslint-disable-next-line no-eval */
      eval(response.data);
    }
  }
}

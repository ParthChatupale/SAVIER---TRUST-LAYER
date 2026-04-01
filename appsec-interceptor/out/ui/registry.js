"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ViewRegistry = void 0;
class ViewRegistry {
    views = new Map();
    register(view) {
        this.views.set(view.id, view);
    }
    get(id) {
        return this.views.get(id);
    }
}
exports.ViewRegistry = ViewRegistry;
//# sourceMappingURL=registry.js.map
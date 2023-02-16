import axios from "axios";

const service = axios.create({
    baseURL: "/api",
    timeout: 8000,
    reportError: true,
});

export default {
    ping: function () {
        return service.get("/ping", {
            timeout: 500,
        });
    },
};

import ws from "k6/ws";
import { check } from "k6";

export const options = {
  vus: 200,
  duration: "1m",
};

export default function () {
  const res = ws.connect(
    "ws://localhost:8000/ws/ws/poll",
    {},
    function (socket) {
      socket.on("open", () => {
        console.log("connected");
      });

      socket.on("message", (msg) => {
        // receives broadcasts
      });

      socket.setTimeout(() => {
        socket.close();
      }, 60000);
    }
  );

  check(res, {
    "connected": (r) => r && r.status === 101,
  });
}
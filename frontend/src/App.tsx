import { useEffect, useRef, useState } from "react";

const Chat: React.FC = () => {
  const [clientId, setClientId] = useState("");

  const [messages, setMessages] = useState<string[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const [currentAIMessage, setCurrentAIMessage] = useState<string>("");

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    setClientId(urlParams.get("id") ?? Date.now().toString());
  }, []) // Runs only initially, as dependency array is empty

  useEffect(() => {
    if (clientId == "") {
      return;
    }
    wsRef.current = new WebSocket(`ws://localhost:8000/ws/${clientId}`)
    console.log(wsRef.current)

    wsRef.current.onmessage = (event: MessageEvent) => {
      if (event.data.startsWith("You:")) {
        if (currentAIMessage) {
          setMessages((prev) => [...prev, currentAIMessage]);
          setCurrentAIMessage("");

        }
        setMessages((prev) => [...prev, currentAIMessage]);
      } else {
        setCurrentAIMessage((prev) => prev + event.data)
      }
    }
  }, [clientId, currentAIMessage]) // Runs whenever clientId gets updated, does nothing if clientId = ""

  return <></>
}

export default Chat;

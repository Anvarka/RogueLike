import com.googlecode.lanterna.input.KeyType
import com.googlecode.lanterna.screen.TerminalScreen
import com.googlecode.lanterna.terminal.DefaultTerminalFactory
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.features.json.*
import io.ktor.client.request.*
import kotlinx.coroutines.runBlocking

class Client(private val user: String, private val screen: TerminalScreen, private val client: HttpClient) {
    private var map: Map

    init {
        connect()
        map = getMapInit()
    }

    fun gameLoop() {
        while (true) {
            map.draw(screen)
            val key = screen.readInput()
            if (key.keyType == KeyType.Escape || key.keyType == KeyType.EOF) {
                return
            }
            if (key.keyType != KeyType.Character) {
                continue
            }
            val dir = when (key.character) {
                'w' -> Direction.UP
                's' -> Direction.DOWN
                'a' -> Direction.LEFT
                'd' -> Direction.RIGHT
                else -> continue
            }
            map = move(dir)
        }
    }

    private fun connect() {
        runBlocking {
            client.post<Unit>("http://localhost:5000/connect") {
                header("Content-Type", "application/json")
                body = UserId(user)
            }
        }
    }

    private fun getMapInit(): Map {
        return runBlocking {
            client.get("http://localhost:5000/map") {
                header("Content-Type", "application/json")
                body = UserId(user)
            }
        }
    }

    private fun move(dir: Direction): Map {
        return runBlocking {
            client.post("http://localhost:5000/move") {
                header("Content-Type", "application/json")
                body = MoveRequest(user, dir)
            }
        }
    }
}

fun main(args: Array<String>) {
    val user = args[0]
    val terminalFactory = DefaultTerminalFactory()
    terminalFactory.createTerminal().use { term ->
        val screen = TerminalScreen(term)
        screen.startScreen()
        screen.cursorPosition = null
        HttpClient(CIO){ install(JsonFeature) }.use { httpClient ->
            val client = Client(user, screen, httpClient)
            client.gameLoop()
        }
    }
}
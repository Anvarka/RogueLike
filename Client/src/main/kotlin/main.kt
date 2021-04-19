import com.googlecode.lanterna.input.KeyType
import com.googlecode.lanterna.screen.TerminalScreen
import com.googlecode.lanterna.terminal.DefaultTerminalFactory
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.features.json.*
import io.ktor.client.request.*
import kotlinx.coroutines.runBlocking

class Client(private val user: String,
             private val screen: TerminalScreen,
             private val client: HttpClient,
             private val server: String) {
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
            client.post<Unit>("$server/server/connect/") {
                header("Content-Type", "application/json")
                body = UserId(user)
            }
        }
    }

    private fun getMapInit(): Map {
        return runBlocking {
            client.post("$server/server/map/") {
                header("Content-Type", "application/json")
                body = UserId(user)
            }
        }
    }

    private fun move(dir: Direction): Map {
        return runBlocking {
            client.post("$server/server/move/") {
                header("Content-Type", "application/json")
                body = MoveRequest(user, dir)
            }
        }
    }
}

fun main(args: Array<String>) {
    if (args.size != 2) {
        System.err.println("usage: ./gradlew run --args=\"NICKNAME SERVER\"")
        return
    }
    val user = args[0]
    val server = args[1]
    val terminalFactory = DefaultTerminalFactory()
    terminalFactory.createTerminal().use { term ->
        val screen = TerminalScreen(term)
        screen.startScreen()
        screen.cursorPosition = null
        HttpClient(CIO){ install(JsonFeature) }.use { httpClient ->
            val client = Client(user, screen, httpClient, server)
            client.gameLoop()
        }
    }
}

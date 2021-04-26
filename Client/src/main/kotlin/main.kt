import com.googlecode.lanterna.input.KeyType
import com.googlecode.lanterna.screen.TerminalScreen
import com.googlecode.lanterna.terminal.DefaultTerminalFactory
import com.googlecode.lanterna.terminal.swing.SwingTerminalFontConfiguration
import com.googlecode.lanterna.TerminalSize
import io.ktor.client.*
import io.ktor.client.engine.cio.*
import io.ktor.client.features.json.*
import io.ktor.client.features.json.serializer.*
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
            if (map.gameOver) {
                screen.clear()
                val graphics = screen.newTextGraphics()
                graphics.putString(4, 10, "Game Over!")
                screen.refresh()
                screen.readInput()
                return
            }
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
    val fontConfig = SwingTerminalFontConfiguration.getDefaultOfSize(25)
    val terminalFactory = DefaultTerminalFactory()
        .setInitialTerminalSize(TerminalSize(20, 20))
        .setTerminalEmulatorFontConfiguration(fontConfig)
    terminalFactory.createTerminal().use { term ->
        val screen = TerminalScreen(term)
        screen.startScreen()
        screen.cursorPosition = null
        HttpClient(CIO){ install(JsonFeature) {
            serializer = KotlinxSerializer(kotlinx.serialization.json.Json {
                ignoreUnknownKeys = true
            })
        }}.use { httpClient ->
            val client = Client(user, screen, httpClient, server)
            client.gameLoop()
        }
    }
}

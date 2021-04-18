import com.googlecode.lanterna.TextCharacter
import com.googlecode.lanterna.screen.TerminalScreen
import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

// Types for serialization

@Serializable
data class Map(val walls: List<List<Int>>, val player: List<Int>) {
    fun draw(screen: TerminalScreen) {
        screen.clear()
        for (wall in walls) {
            screen.setCharacter(wall[0], wall[1], TextCharacter.fromCharacter('#')[0])
        }
        screen.setCharacter(player[0], player[1], TextCharacter.fromCharacter('@')[0])
        screen.refresh()
    }
}

@Serializable
data class UserId(@SerialName("user_id") val userId: String)

@Serializable
enum class Direction {
    @SerialName("up") UP,
    @SerialName("down") DOWN,
    @SerialName("left") LEFT,
    @SerialName("right") RIGHT
}

@Serializable
data class MoveRequest(val user_id: String, val direction: Direction)
import React from "react";
import { Link } from "react-router-dom";
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  Container,
  Button,
  FormControl,
  Select,
  MenuItem,
  InputLabel,
  IconButton,
  Tooltip,
} from "@mui/material";
import ChatIcon from "@mui/icons-material/Chat";
import GitHubIcon from "@mui/icons-material/GitHub";
import SettingsIcon from "@mui/icons-material/Settings";
import { colors } from "../App";

const Header = ({ dataSource, onDataSourceChange, isLoading }) => {
  return (
    <AppBar position="static" sx={{ mb: 4 }}>
      <Container>
        <Toolbar sx={{ p: { xs: 1, sm: 1.5 }, px: { xs: 1, sm: 0 } }}>
          <Box
            component={Link}
            to="/"
            sx={{
              display: "flex",
              alignItems: "center",
              textDecoration: "none",
              color: "inherit",
              flexGrow: 1,
              "&:hover": {
                textDecoration: "none",
              },
            }}
          >
            <ChatIcon sx={{ mr: 1.5, fontSize: 28 }} />
            <Typography variant="h5" component="div" fontWeight="700">
              AI IDE Chat Export Tool
            </Typography>
          </Box>

          {/* 数据源选择器 */}
          <FormControl
            variant="outlined"
            size="small"
            sx={{
              mr: 2,
              minWidth: 160,
              "& .MuiOutlinedInput-root": {
                color: "white",
                "& fieldset": {
                  borderColor: "rgba(255,255,255,0.5)",
                },
                "&:hover fieldset": {
                  borderColor: "rgba(255,255,255,0.8)",
                },
                "&.Mui-focused fieldset": {
                  borderColor: colors.highlightColor,
                },
              },
              "& .MuiInputLabel-root": {
                color: "rgba(255,255,255,0.7)",
                "&.Mui-focused": {
                  color: colors.highlightColor,
                },
              },
              "& .MuiSelect-icon": {
                color: "white",
              },
            }}
          >
            <InputLabel id="data-source-label">数据源</InputLabel>
            <Select
              labelId="data-source-label"
              value={dataSource}
              label="数据源"
              onChange={(e) => onDataSourceChange(e.target.value)}
              disabled={isLoading}
              sx={{
                "& .MuiSelect-select": {
                  color: "white",
                },
              }}
            >
              <MenuItem value="cursor">Cursor</MenuItem>
              <MenuItem value="augment">VSCode Augment</MenuItem>
              <MenuItem value="cursor-augment">Cursor Augment</MenuItem>
              <MenuItem value="idea-augment">IDEA Augment</MenuItem>
              <MenuItem value="pycharm-augment">PyCharm Augment</MenuItem>
            </Select>
          </FormControl>

          {/* 设置按钮 */}
          <Tooltip title="设置">
            <IconButton
              component={Link}
              to="/settings"
              color="inherit"
              sx={{
                color: "white",
                "&:hover": {
                  backgroundColor: colors.highlightColor,
                },
              }}
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>

          <Button
            component="a"
            href="https://github.com/wangxin776/AI-IDE-Chat-Export-Tool"
            target="_blank"
            rel="noopener noreferrer"
            startIcon={<GitHubIcon />}
            variant="outlined"
            color="inherit"
            size="small"
            sx={{
              borderColor: "rgba(255,255,255,0.5)",
              color: "white",
              "&:hover": {
                borderColor: "rgba(255,255,255,0.8)",
                backgroundColor: colors.highlightColor,
              },
            }}
          >
            GitHub
          </Button>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Header;

import React, { useState } from "react";
import {
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Box,
  Chip,
  Alert,
  Collapse,
  IconButton,
  Tooltip,
  List,
  ListItem,
  ListItemText,
} from "@mui/material";
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  RestoreFromTrash as ResetIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  Folder as FolderIcon,
  Info as InfoIcon,
} from "@mui/icons-material";

const PathConfigCard = ({
  dataSource,
  currentPath,
  defaultPath,
  validationResult,
  onPathChange,
  onValidate,
  onReset,
}) => {
  const [localPath, setLocalPath] = useState(currentPath);
  const [validating, setValidating] = useState(false);
  const [showDetails, setShowDetails] = useState(false);

  // 处理路径输入变化
  const handlePathChange = (event) => {
    const newPath = event.target.value;
    setLocalPath(newPath);
    onPathChange(newPath);
  };

  // 验证路径
  const handleValidate = async () => {
    setValidating(true);
    await onValidate(localPath);
    setValidating(false);
  };

  // 重置路径
  const handleReset = () => {
    onReset();
    setLocalPath("");
  };

  // 获取验证状态
  const getValidationStatus = () => {
    if (!validationResult) {
      return { icon: null, color: "default", text: "未验证" };
    }

    if (validationResult.is_valid) {
      return {
        icon: <CheckIcon />,
        color: "success",
        text: "有效",
      };
    } else {
      return {
        icon: <ErrorIcon />,
        color: "error",
        text: "无效",
      };
    }
  };

  const validationStatus = getValidationStatus();

  // 获取显示的路径（当前路径或默认路径）
  const displayPath = localPath || defaultPath || "未设置";
  const isUsingDefault = !localPath && defaultPath;

  return (
    <Card elevation={2} sx={{ mb: 2 }}>
      <CardContent>
        {/* 卡片标题 */}
        <Box
          display="flex"
          alignItems="center"
          justifyContent="space-between"
          mb={2}
        >
          <Box display="flex" alignItems="center">
            <FolderIcon sx={{ mr: 1, color: "primary.main" }} />
            <Typography variant="h6" component="h3">
              {dataSource.displayName}
            </Typography>
          </Box>

          {/* 验证状态指示器 */}
          {validationStatus.icon && (
            <Chip
              icon={validationStatus.icon}
              label={validationStatus.text}
              color={validationStatus.color}
              size="small"
            />
          )}
        </Box>

        {/* 描述 */}
        <Typography variant="body2" color="text.secondary" mb={2}>
          {dataSource.description}
        </Typography>

        {/* 路径输入框 */}
        <TextField
          fullWidth
          label="自定义路径"
          placeholder={defaultPath || "使用系统默认路径"}
          value={localPath}
          onChange={handlePathChange}
          variant="outlined"
          size="small"
          sx={{ mb: 2 }}
          helperText={
            isUsingDefault
              ? `当前使用默认路径: ${defaultPath}`
              : localPath
              ? "使用自定义路径"
              : "留空使用默认路径"
          }
        />

        {/* 操作按钮 */}
        <Box display="flex" gap={1} flexWrap="wrap" mb={2}>
          <Button
            variant="outlined"
            size="small"
            onClick={handleValidate}
            disabled={validating}
            startIcon={
              validating ? <RefreshIcon className="spin" /> : <RefreshIcon />
            }
          >
            {validating ? "验证中..." : "验证路径"}
          </Button>

          <Button
            variant="outlined"
            size="small"
            color="warning"
            onClick={handleReset}
            startIcon={<ResetIcon />}
          >
            重置
          </Button>

          {validationResult && (
            <Button
              variant="text"
              size="small"
              onClick={() => setShowDetails(!showDetails)}
              endIcon={showDetails ? <ExpandLessIcon /> : <ExpandMoreIcon />}
            >
              {showDetails ? "隐藏详情" : "显示详情"}
            </Button>
          )}
        </Box>

        {/* 验证结果 */}
        {validationResult && (
          <>
            <Alert
              severity={validationResult.is_valid ? "success" : "error"}
              sx={{ mb: 2 }}
              icon={validationResult.is_valid ? <CheckIcon /> : <ErrorIcon />}
            >
              {validationResult.message}
            </Alert>

            {/* 详细信息 */}
            <Collapse in={showDetails}>
              <Box sx={{ mt: 2, p: 2, bgcolor: "grey.50", borderRadius: 1 }}>
                <Typography variant="subtitle2" gutterBottom>
                  验证详情
                </Typography>

                {/* 找到的文件 */}
                {validationResult.found_files &&
                  validationResult.found_files.length > 0 && (
                    <Box mb={2}>
                      <Typography
                        variant="body2"
                        fontWeight="medium"
                        gutterBottom
                      >
                        找到的文件/目录:
                      </Typography>
                      <List dense>
                        {validationResult.found_files.map((file, index) => (
                          <ListItem key={index} sx={{ py: 0.5 }}>
                            <ListItemText
                              primary={file}
                              primaryTypographyProps={{
                                variant: "body2",
                                fontFamily: "monospace",
                              }}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </Box>
                  )}

                {/* 技术详情 */}
                {validationResult.details &&
                  Object.keys(validationResult.details).length > 0 && (
                    <Box>
                      <Typography
                        variant="body2"
                        fontWeight="medium"
                        gutterBottom
                      >
                        技术详情:
                      </Typography>
                      <Box
                        component="pre"
                        sx={{
                          fontSize: "0.75rem",
                          fontFamily: "monospace",
                          bgcolor: "grey.100",
                          p: 1,
                          borderRadius: 1,
                          overflow: "auto",
                          maxHeight: "200px",
                        }}
                      >
                        {JSON.stringify(validationResult.details, null, 2)}
                      </Box>
                    </Box>
                  )}
              </Box>
            </Collapse>
          </>
        )}

        {/* 默认路径信息 */}
        {defaultPath && (
          <Box
            sx={{
              mt: 2,
              p: 2,
              bgcolor: "rgba(33, 150, 243, 0.1)",
              border: "1px solid rgba(33, 150, 243, 0.3)",
              borderRadius: 1,
            }}
          >
            <Box display="flex" alignItems="center" mb={1}>
              <InfoIcon sx={{ mr: 1, fontSize: "small", color: "info.main" }} />
              <Typography
                variant="body2"
                fontWeight="medium"
                color="text.primary"
              >
                系统默认路径
              </Typography>
            </Box>
            <Typography
              variant="body2"
              sx={{
                fontFamily: "monospace",
                wordBreak: "break-all",
                color: "text.primary",
                opacity: 0.8,
              }}
            >
              {defaultPath}
            </Typography>
          </Box>
        )}
      </CardContent>

      {/* CSS for spinning animation */}
      <style jsx>{`
        @keyframes spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
        .spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </Card>
  );
};

export default PathConfigCard;
